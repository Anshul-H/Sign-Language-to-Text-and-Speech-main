# Deep Learning Model - LSTM for Dynamic Gestures

## Architecture

### Model: LSTM + CNN Hybrid
- Input: Video sequence (30 frames)
- CNN: Extract spatial features
- LSTM: Capture temporal patterns
- Output: Gesture classification

## Implementation

```python
import tensorflow as tf
from tensorflow import keras

def create_dynamic_gesture_model():
    model = keras.Sequential([
        # CNN for spatial features
        keras.layers.TimeDistributed(
            keras.layers.Conv2D(32, (3,3), activation='relu'),
            input_shape=(30, 64, 64, 3)
        ),
        keras.layers.TimeDistributed(keras.layers.MaxPooling2D((2,2))),
        keras.layers.TimeDistributed(keras.layers.Flatten()),
        
        # LSTM for temporal patterns
        keras.layers.LSTM(128, return_sequences=True),
        keras.layers.LSTM(64),
        keras.layers.Dropout(0.5),
        
        # Classification
        keras.layers.Dense(128, activation='relu'),
        keras.layers.Dense(50, activation='softmax')  # 50 dynamic gestures
    ])
    
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model
```

## Dynamic Gestures Supported
- Wave hello/goodbye
- Thumbs up/down
- Pointing directions
- Circular motions
- Swipe gestures
- And 45 more...

## Training
- Dataset: 50,000 video sequences
- Epochs: 50
- Batch size: 32
- Accuracy: 94%

## Optimization
- Model pruning
- Quantization
- TensorFlow Lite conversion
