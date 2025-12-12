import json 
import tensorflow as tf 
from tensorflow.keras import layers, models 
from tensorflow.keras.preprocessing.image import ImageDataGenerator 
from tensorflow.keras.applications import MobileNetV2 
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input 

DATA_DIR = "data" 
IMG_SIZE = (224, 224) 
BATCH_SIZE = 32 
VAL_SPLIT = 0.2 
SEED = 42 

EPOCHS_STAGE1 = 10 
EPOCHS_STAGE2 = 5 

# MobileNetV2 권장 전처리 + 증강 
datagen = ImageDataGenerator( 
    preprocessing_function=preprocess_input, 
    validation_split=VAL_SPLIT, 
    rotation_range=10, 
    width_shift_range=0.05, 
    height_shift_range=0.05, 
    zoom_range=0.1, 
    horizontal_flip=True, 
) 

train_data = datagen.flow_from_directory( 
    DATA_DIR, 
    target_size=IMG_SIZE, 
    batch_size=BATCH_SIZE, 
    subset="training", 
    seed=SEED, 
    shuffle=True, 
    class_mode="categorical", 
) 

val_data = datagen.flow_from_directory( 
    DATA_DIR, 
    target_size=IMG_SIZE, 
    batch_size=BATCH_SIZE, 
    subset="validation", 
    seed=SEED, 
    shuffle=False, 
    class_mode="categorical", 
) 

num_classes = len(train_data.class_indices) 

# 라벨 매핑 저장 (추론에서 그대로 사용) 
with open("class_indices.json", "w", encoding="utf-8") as f: 
    json.dump(train_data.class_indices, f, 
              ensure_ascii=False, indent=2) 
    
base = MobileNetV2( 
    weights="imagenet", 
    include_top=False, 
    input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3), 
) 
base.trainable = False 

inputs = layers.Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3)) 
x = base(inputs, training=False) 
x = layers.GlobalAveragePooling2D()(x) 
x = layers.Dropout(0.2)(x) 
outputs = layers.Dense(num_classes, activation="softmax")(x) 

model = models.Model(inputs, outputs) 
model.compile( 
    optimizer=tf.keras.optimizers.Adam(1e-3), 
    loss="categorical_crossentropy", 
    metrics=["accuracy"], 
) 

callbacks = [ 
    tf.keras.callbacks.EarlyStopping(monitor="loss", patience=3, restore_best_weights=True),
    tf.keras.callbacks.ReduceLROnPlateau(monitor="loss", patience=2, factor=0.5, min_lr=1e-6),
    tf.keras.callbacks.ModelCheckpoint("my_model.h5", monitor="loss", save_best_only=True),
] 

#1단계: 헤드만 학습 
model.fit( 
    train_data, 
    epochs=EPOCHS_STAGE1, 
    callbacks=callbacks, 
) 

# 2단계: 일부 파인튜닝(데이터 적으면 생략 가능) 
base.trainable = True 
for layer in base.layers[:-30]: 
    layer.trainable = False 

model.compile( 
    optimizer=tf.keras.optimizers.Adam(1e-4), 
    loss="categorical_crossentropy", 
    metrics=["accuracy"], 
) 

model.fit( 
    train_data, 
    epochs=EPOCHS_STAGE2, 
    callbacks=callbacks, 
) 

print("Saved my_model.h5 and class_indices.json")