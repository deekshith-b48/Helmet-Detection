# Helmet Detection Project

This project aims to develop a computer vision model that can detect whether a person is wearing a helmet or not, using real-time video feeds or images. This is crucial for ensuring safety standards in various scenarios such as construction sites, bike riding, and more.

## Project Structure

```
├── config/
│   └── config.yaml         # Configuration file for model paths, thresholds, etc.
├── data/
│   ├── images/             # Directory for storing image datasets
│   └── videos/             # Directory for storing video datasets
├── models/                 # Directory for storing trained model files
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── helmet_detector.py    # Core logic for helmet detection
│   │   └── violation_detector.py # Logic for identifying violations
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── db_manager.py         # Database interaction logic
│   │   └── notifier.py           # Notification system (e.g., email alerts)
│   └── __init__.py
├── tests/
│   ├── unit/                 # Unit tests for individual modules
│   └── integration/          # Integration tests (optional)
├── .gitignore              # Specifies intentionally untracked files that Git should ignore
├── detect_helmet.py        # Main script to run detection on webcam/video
├── train_model.py          # Script to train the helmet detection model
├── evaluate_model.py       # Script to evaluate the trained model
├── requirements.txt        # Python package dependencies
└── README.md               # This file
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd helmet-detection-project
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Configuration (`config/config.yaml`)

The main configuration for the project is managed in `config/config.yaml`. Key sections include:

*   **`model`**:
    *   `name`, `path`: Specify the YOLO model to be used. Can be a standard model (e.g., `yolov8n.pt`) or a path to a custom-trained model.
    *   `confidence_threshold`, `iou_threshold`: Detection parameters.
    *   `active_class_set_type`: Set to `"coco"` for generic COCO models or `"custom_helmet"` for models trained specifically for helmet detection. This determines how `classes` are interpreted.
    *   `classes`: A mapping of human-readable class names to the integer class IDs used by the currently active model (e.g., `{'person': 0}` for COCO, or `{'helmet': 0, 'no_helmet': 1}` for a custom model).
    *   `violation_relevant_classes`: Defines which classes from the `classes` map should trigger a violation or be flagged by the `ViolationDetector` (e.g., `{'person': "person"}` for COCO, or `{'no_helmet': "no_helmet"}` for a custom model).
*   **`detection`**: Settings for real-time detection, like resolution and whether to show video.
*   **`data`**:
    *   `dataset_yaml`: **Crucial for training/evaluation.** Path to your dataset's `.yaml` file (YOLOv5/v8 format), which defines paths to train/val/test image sets and class names.
*   **`training`**: Default parameters for training, such as epochs, batch size, image size (`imgsz`), optimizer, and learning rate. These can often be overridden by CLI arguments in `train_model.py`.
*   **`database`** and **`notifications`**: Configurations for (optional) database logging and alert notifications.

### Running Detection

The `detect_helmet.py` script uses the `YOLOHelmetDetector` to perform detections and the `ViolationDetector` to interpret these detections based on the active configuration in `config/config.yaml`.

*   **Using Webcam:**
    ```bash
    python detect_helmet.py --config_path config/config.yaml
    ```
*   **Using a Video File:**
    ```bash
    python detect_helmet.py --video_path /path/to/your/video.mp4 --config_path config/config.yaml
    ```
    Detections will be color-coded:
    *   **Orange (Person Sighting):** If using a generic COCO model, detected persons are highlighted.
    *   **Red (Violation):** If using a custom helmet model, 'no_helmet' detections are highlighted.
    *   **Green (Compliant/Neutral):** 'helmet' detections (custom model) or other non-violating detections.

### Training a New Model (`train_model.py`)

1.  **Prepare Your Dataset:**
    *   Organize your images (train/val) and labels in YOLO format.
    *   Create a `dataset.yaml` file (e.g., `data/helmet_dataset.yaml`) defining paths and class names. Example:
        ```yaml
        path: ../data/helmet_dataset  # Root directory of the dataset
        train: images/train  # Training images (relative to 'path')
        val: images/val    # Validation images (relative to 'path')
        # test: images/test  # Optional test images

        nc: 2  # Number of classes
        names: ['helmet', 'no_helmet']  # Class names
        ```
    *   Update `data.dataset_yaml` in `config/config.yaml` to point to this file, or provide it via CLI.

2.  **Configure Training:**
    *   Adjust parameters in the `training` section of `config/config.yaml` (epochs, batch size, image size, etc.).
    *   Choose a base model for training/fine-tuning in `model.path` or `model.name` (e.g., `yolov8n.pt` for fine-tuning, or `yolov8n.yaml` to train from scratch).

3.  **Run the Training Script:**
    ```bash
    python train_model.py --dataset_yaml path/to/your/dataset.yaml --app_config config/config.yaml
    ```
    *   **CLI Overrides:** Many parameters can be overridden via command-line arguments. Use `python train_model.py --help` for details.
        *   `--model_path`: Specify a base model (e.g., `yolov8n.pt`, `yolov8s.yaml`).
        *   `--epochs`, `--batch_size`, `--img_size`, `--optimizer`, `--lr`, `--device`.
        *   `--project_name`, `--experiment_name`: For organizing training runs.
    *   Trained models are typically saved under `runs/train/YOUR_EXPERIMENT_NAME/weights/best.pt`.

### Evaluating a Trained Model (`evaluate_model.py`)

1.  **Ensure Model and Dataset are Ready:**
    *   You need a trained model file (e.g., `runs/train/exp/weights/best.pt`).
    *   Your `dataset.yaml` (used during training) should also define a validation set (and optionally a test set).

2.  **Run the Evaluation Script:**
    ```bash
    python evaluate_model.py --model_path path/to/your/trained_model.pt --dataset_yaml path/to/your/dataset.yaml --app_config config/config.yaml
    ```
    *   **CLI Overrides:**
        *   `--img_size`, `--batch_size`, `--conf_thres`, `--iou_thres`, `--device`.
        *   `--split`: Choose dataset split for evaluation (`val` or `test`, default is `val`).
        *   `--project_name`, `--experiment_name`: For organizing evaluation runs.
    *   Evaluation metrics (mAP, precision, recall) will be printed, and detailed results saved under `runs/val/YOUR_EXPERIMENT_NAME`.

## Core Modules

*   **`src/core/helmet_detector.py` (`YOLOHelmetDetector`):** Loads a YOLO model (from `ultralytics`) and performs object detection on input frames. Interprets class IDs based on `config.yaml`.
*   **`src/core/violation_detector.py` (`ViolationDetector`):** Processes detections from `YOLOHelmetDetector`. Based on `config.yaml` (`active_class_set_type` and `violation_relevant_classes`), it identifies and flags violations (e.g., "no_helmet" from a custom model) or persons of interest ("person_sighting" from a COCO model).
*   **`src/utils/db_manager.py` (`DBManager`):** Placeholder for database interaction logic (e.g., logging violations).
*   **`src/utils/notifier.py` (`NotificationManager`):** Existing advanced module for sending notifications (e.g., email alerts for violations). Not fully integrated into the detection pipeline's flow yet.

## Next Steps
*   Integrate `DBManager` and `NotificationManager` into the main detection loop in `detect_helmet.py` to log violations and send alerts.
*   Flesh out unit tests for the core components.
*   Prepare a sample helmet/no-helmet dataset and `dataset.yaml` to demonstrate custom training.
*   Refine error handling and logging throughout the application.
*   Consider adding support for different types of YOLO models or other detection frameworks if needed.

## Contributing
Details on how to contribute will be added later. If you'd like to contribute, please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License - see the `LICENSE` file for details (To be added).
