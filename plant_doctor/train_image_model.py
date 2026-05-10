import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
import json

# Configuration
DATASET_DIR = 'Dataset'
MODEL_SAVE_PATH = 'crop_model.h5'
TREATMENTS_JSON = 'treatments.json'
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 10  # Low epochs for demonstration/quick training

def train_model():
    print("🚀 Starting Plant Doctor Image Model Training...")
    
    if not os.path.exists(DATASET_DIR):
        print(f"❌ Error: Dataset directory not found at {DATASET_DIR}")
        return

    # Data Augmentation
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        validation_split=0.2
    )

    print(f"📦 Loading images from {DATASET_DIR}...")
    train_generator = train_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='training'
    )

    validation_generator = train_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='validation'
    )

    num_classes = len(train_generator.class_indices)
    print(f"✅ Found {num_classes} classes.")

    # Save class names to treatments.json if not already there
    class_names = sorted(list(train_generator.class_indices.keys()))
    with open(TREATMENTS_JSON, 'r') as f:
        treatments_data = json.load(f)
    
    treatments_data['class_names'] = class_names
    with open(TREATMENTS_JSON, 'w') as f:
        json.dump(treatments_data, f, indent=4)
    print(f"📝 Updated {TREATMENTS_JSON} with {len(class_names)} classes.")

    # Model Architecture (Transfer Learning)
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(*IMG_SIZE, 3))
    base_model.trainable = False  # Freeze base model

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(512, activation='relu')(x)
    x = Dropout(0.5)(x)
    predictions = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=base_model.input, outputs=predictions)

    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

    # Callbacks
    checkpoint = ModelCheckpoint(MODEL_SAVE_PATH, monitor='val_accuracy', save_best_only=True, mode='max', verbose=1)
    early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

    print("🏋️ Training starting...")
    model.fit(
        train_generator,
        epochs=EPOCHS,
        validation_data=validation_generator,
        callbacks=[checkpoint, early_stop]
    )

    print(f"🎉 Training complete! Model saved to {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_model()
