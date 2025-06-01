
## AI2002 – Artificial Intelligence

## Project: TORCS – The Open Racing Car Simulator

---

### Team Members

- [Emi-Pemi](https://github.com/Emi-Pemi)
- [SaraAkbar16](https://github.com/SaraAkbar16)
- [NNoorFatima](https://github.com/NNoorFatima)


---

## Data Preprocessing and Training

### Dataset Loading

- Loads the CSV file into a Pandas DataFrame named `df`.
- Each row represents one time-step of driving data.
- Each column is a feature (e.g., speed, track sensors) or target output (e.g., steering, acceleration).

### Feature and Target Separation

- `y_columns` lists the output variables the neural network will predict.
- `X_columns` automatically grabs all other columns as input features (by excluding `y_columns`).

### Handling Missing Data

- Ensures rows with missing (`NaN`) values are removed to maintain clean input for the neural network.

### Convert to PyTorch Tensors

- Converts DataFrame data into `float32` tensors.
  - `X`: Input features (e.g., track sensors, speed, RPM)
  - `y`: Target outputs (e.g., steering, acceleration)

### Train/Validation Split

- Wraps `X` and `y` into a `TensorDataset` for PyTorch’s `DataLoader`.
- Randomly splits the dataset:
  - 80% for training
  - 20% for validation

### Create DataLoaders

- `train_loader`: Batches of 64, shuffled each epoch.
- `val_loader`: Batches (not shuffled), used for evaluation.

---

## Neural Network for Driving Control Prediction

### 1. Objective

Train a neural network to predict driving control actions based on input features:

- Acceleration (`accel`)
- Braking (`Braking`)
- Clutch (`Clutch`)
- Gear (`Gear`)
- Steering (`Steering`)

A Multi-Layer Perceptron (MLP) is used to predict these outputs from driving-related sensor data.

### 2. Dataset Overview

- Dataset: `Dataset.csv`
- Each row contains telemetry data with features and output control actions.
- Preprocessed and split into training and validation sets.

---

## ⚙️ Data Preprocessing Details

### 3.1 Data Loading

- Loaded using Pandas into a DataFrame.

### 3.2 Feature Selection

**Target Variables (`y_columns`):**
- `accel`
- `Braking`
- `Clutch`
- `Gear`
- `Steering`

**Input Variables (`X_columns`):**
- All other columns excluding `y_columns`.

### 3.3 Handling Missing Data

- Drops rows with `NaN` values for clean training data.

### 3.4 Conversion to PyTorch Tensors

- Converts both input and output DataFrames to PyTorch tensors.

### 3.5 Splitting Data

- 80% training / 20% validation using `random_split`.

---

## Model Architecture

### 4.1 Multi-Layer Perceptron (MLP)

- **Input Layer**: Number of features = length of `X_columns`
- **Hidden Layers**:
  - Layer 1: 128 neurons, ReLU activation
  - Layer 2: 64 neurons, ReLU activation
- **Output Layer**: 5 neurons for 5 outputs

### 4.2 Loss and Optimizer

- **Loss Function**: Mean Squared Error (MSE)
- **Optimizer**: Adam (learning rate = 0.001)

---

## Training Process

### 5.1 Training Loop

- Trained for **50 epochs**
- Each epoch includes:
  - **Training**:
    - Forward pass
    - MSE loss calculation
    - Backpropagation
  - **Validation**:
    - Evaluated on validation data
    - Validation loss monitored to track generalization

### 5.2 Epoch Output

- After each epoch, validation loss is printed.

---

## Model Saving

- Trained model weights saved to file: `mlp_controller_model.pth`
- Can be loaded later for inference or further training.

---

## Evaluation and Results

- Validation loss is tracked throughout training.
- A lower validation loss implies better generalization.
- The process helps detect underfitting/overfitting.

---

## Conclusion

This project implements a Multi-Layer Perceptron (MLP) model to predict continuous control outputs (acceleration, braking, clutch, gear, steering) from telemetry data.

- Trained using MSE loss and Adam optimizer.
- Evaluated on a validation set.
- Model is saved for future inference or fine-tuning.

---

##  Running Command

Run the following command in your terminal:

```bash
python pyclient.py
