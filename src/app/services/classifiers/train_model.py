import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models

from sklearn.utils import class_weight
import numpy as np

# 사전 훈련된 MobileNetV2 모델 로드
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

# 모델을 학습하지 않도록 고정
base_model.trainable = False

# 새로운 분류기 추가
model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(128, activation='relu'),
    layers.Dense(1, activation='sigmoid')  # 거북목 (forward_head)과 정상 (normal)을 분류
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# 데이터 준비 (데이터 증강)
train_datagen = ImageDataGenerator(
    rescale=1./255,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    rotation_range=40,  # 데이터 증강: 회전
    width_shift_range=0.2,  # 데이터 증강: 가로 이동
    height_shift_range=0.2  # 데이터 증강: 세로 이동
)

validation_datagen = ImageDataGenerator(rescale=1./255)

# 학습 데이터 및 검증 데이터 불러오기
train_data = train_datagen.flow_from_directory('data/train', target_size=(224, 224), batch_size=32, class_mode='binary')
validation_data = validation_datagen.flow_from_directory('data/validation', target_size=(224, 224), batch_size=32, class_mode='binary')

# 클래스 가중치 계산 (불균형한 클래스에 대해 가중치를 조정)
class_weights = class_weight.compute_class_weight(
    'balanced', 
    classes=np.unique(train_data.classes), 
    y=train_data.classes
)

class_weights_dict = {0: class_weights[0], 1: class_weights[1]}  # 정상 자세: 0, 거북목 자세: 1

# 모델 학습 (class_weight 적용)
history = model.fit(
    train_data, 
    epochs=10, 
    validation_data=validation_data,
    class_weight=class_weights_dict  # 클래스별 가중치 반영
)

# 모델 저장
model.save('forward_head_model.h5')

# 학습된 모델 평가
test_loss, test_accuracy = model.evaluate(validation_data)
print(f"Test Accuracy: {test_accuracy}")