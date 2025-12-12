import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models

# 1. 사전 훈련된 MobileNetV2 모델 로드
# (include_top=False는 마지막 분류 계층을 제외한 모델)
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

# 2. 모델을 학습하지 않도록 고정
base_model.trainable = False

# 3. 새로운 분류기 추가
model = models.Sequential([
    base_model,  # MobileNetV2
    layers.GlobalAveragePooling2D(),  # 평균 풀링
    layers.Dense(128, activation='relu'),  # 추가적인 레이어
    layers.Dense(1, activation='sigmoid')  # 이진 분류 (거북목 vs 정상)
])

# 4. 모델 컴파일
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# 5. 데이터 준비 (이미지 전처리 및 데이터 증강)
train_datagen = ImageDataGenerator(rescale=1./255, shear_range=0.2, zoom_range=0.2, horizontal_flip=True)
validation_datagen = ImageDataGenerator(rescale=1./255)

# 6. 훈련 및 검증 데이터 로드
train_data = train_datagen.flow_from_directory(
    'data/train', 
    target_size=(224, 224), 
    batch_size=32, 
    class_mode='binary'  # 이진 분류
)

validation_data = validation_datagen.flow_from_directory(
    'data/validation', 
    target_size=(224, 224), 
    batch_size=32, 
    class_mode='binary'  # 이진 분류
)

# 7. 모델 학습
history = model.fit(
    train_data, 
    epochs=10,  # 학습 횟수
    validation_data=validation_data  # 검증 데이터
)

# 8. 학습된 모델 저장
model.save('forward_head_model.h5')