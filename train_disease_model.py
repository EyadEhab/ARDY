import os
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.applications import EfficientNetB0
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DATASET_PATH = 'Plant Doctor/Dataset'
MODEL_SAVE_PATH = 'models/crop_model.h5'
IMG_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 5  # Reduced for stability in container environment

def train_model():
    logger.info("Starting disease model training...")
    
    # 1. Load Dataset
    current_dataset_path = DATASET_PATH
    if not os.path.exists(current_dataset_path):
        logger.error(f"Dataset path not found: {current_dataset_path}")
        # Try lowercase or alternative
        alt_path = current_dataset_path.lower()
        if os.path.exists(alt_path):
            logger.info(f"Found alternative path: {alt_path}")
            current_dataset_path = alt_path
        else:
            logger.error("No valid dataset path found. Exiting.")
            import sys
            sys.exit(1)

    logger.info(f"Loading dataset from {current_dataset_path}")
    try:
        train_ds = tf.keras.utils.image_dataset_from_directory(
            current_dataset_path,
            validation_split=0.2,
            subset="training",
            seed=123,
            image_size=IMG_SIZE,
            batch_size=BATCH_SIZE,
            label_mode='categorical'
        )
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        import sys
        sys.exit(1)
    
    val_ds = tf.keras.utils.image_dataset_from_directory(
        current_dataset_path,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        label_mode='categorical'
    )
    
    class_names = train_ds.class_names
    num_classes = len(class_names)
    logger.info(f"Found {num_classes} classes: {class_names}")
    
    # 2. Performance Optimizations
    AUTOTUNE = tf.data.AUTOTUNE
    # Removed .cache() to prevent OOM in resource-constrained container environments
    train_ds = train_ds.shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)
    
    # 3. Build Model (EfficientNetB0)
    logger.info("Building EfficientNetB0 model...")
    base_model = EfficientNetB0(include_top=False, weights='imagenet', input_shape=(*IMG_SIZE, 3))
    
    # Freeze base model initially
    base_model.trainable = False
    
    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.BatchNormalization(),
        layers.Dropout(0.2),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-3),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # 4. Initial Training (Top layers)
    logger.info("Training top layers...")
    model.fit(train_ds, validation_data=val_ds, epochs=3)
    
    # 5. Fine-tuning (Unfreeze last 20% of layers)
    logger.info("Fine-tuning: Unfreezing last 20% of layers...")
    base_model.trainable = True
    # EfficientNetB0 has ~237 layers. 20% is ~47 layers.
    fine_tune_at = int(len(base_model.layers) * 0.8)
    for layer in base_model.layers[:fine_tune_at]:
        layer.trainable = False
        
    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-5), # Lower learning rate for fine-tuning
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    logger.info("Starting fine-tuning...")
    model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS)
    
    # 6. Save Model
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    model.save(MODEL_SAVE_PATH)
    logger.info(f"Model saved to {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_model()
