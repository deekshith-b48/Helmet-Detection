import argparse
import yaml
import os
from ultralytics import YOLO

def load_app_config(config_path="config/config.yaml"):
    """Loads the main application configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Main configuration file not found: {config_path}")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def train_yolo_model(app_config, dataset_yaml_path, cli_args):
    """
    Trains a YOLO model using the ultralytics library.

    Args:
        app_config (dict): The main application configuration.
        dataset_yaml_path (str): Path to the dataset's .yaml file (YOLO format).
        cli_args (argparse.Namespace): Command-line arguments.
    """
    model_config = app_config.get('model', {})
    training_config = app_config.get('training', {})

    # Determine model to use:
    # 1. From CLI argument if provided
    # 2. From app_config 'model.path' if it's a .pt file (implies fine-tuning or resuming)
    # 3. From app_config 'model.name' (e.g., 'yolov8n.yaml' for from scratch, 'yolov8n.pt' for pre-trained)

    model_to_load = cli_args.model_path if cli_args.model_path else model_config.get('path', 'yolov8n.pt')
    if not model_to_load.endswith(".pt") and not model_to_load.endswith(".yaml"):
        # Assuming it's a base model name like 'yolov8n', append '.pt' to imply using pre-trained weights
        print(f"Warning: Model name '{model_to_load}' does not end with .pt or .yaml. Assuming pre-trained '{model_to_load}.pt'.")
        model_to_load = f"{model_to_load}.pt"

    print(f"Attempting to load model: {model_to_load}")
    try:
        model = YOLO(model_to_load)
        print(f"Successfully loaded model: {model_to_load}")
    except Exception as e:
        print(f"Error loading model {model_to_load}. Attempting default yolov8n.pt. Error: {e}")
        try:
            model = YOLO('yolov8n.pt') # Fallback
            print("Successfully loaded default yolov8n.pt for training.")
        except Exception as e2:
            print(f"Failed to load any model. Error: {e2}")
            raise

    # Override config epochs and batch_size with CLI args if provided
    epochs = cli_args.epochs if cli_args.epochs is not None else training_config.get('epochs', 50)
    batch_size = cli_args.batch_size if cli_args.batch_size is not None else training_config.get('batch_size', 16)
    imgsz = cli_args.img_size if cli_args.img_size is not None else training_config.get('imgsz', 640)

    # Other training parameters from app_config.training or CLI
    optimizer = cli_args.optimizer if cli_args.optimizer else training_config.get('optimizer', 'auto') # 'auto' lets ultralytics choose
    learning_rate = cli_args.lr if cli_args.lr is not None else training_config.get('learning_rate', None) # None uses ultralytics default
    project_name = cli_args.project_name if cli_args.project_name else "runs/train"
    experiment_name = cli_args.experiment_name if cli_args.experiment_name else "exp"
    device = cli_args.device if cli_args.device else '' # '' for auto-select (GPU if available)

    print("\n--- Training Configuration ---")
    print(f"  Model: {model_to_load}")
    print(f"  Dataset YAML: {dataset_yaml_path}")
    print(f"  Epochs: {epochs}")
    print(f"  Batch Size: {batch_size}")
    print(f"  Image Size: {imgsz}")
    print(f"  Optimizer: {optimizer}")
    print(f"  Learning Rate: {learning_rate if learning_rate else 'Ultralytics Default'}")
    print(f"  Device: {'Auto-select' if not device else device}")
    print(f"  Project Directory: {project_name}")
    print(f"  Experiment Name: {experiment_name}")
    print("----------------------------\n")

    try:
        model.train(
            data=dataset_yaml_path,
            epochs=epochs,
            batch=batch_size,
            imgsz=imgsz,
            optimizer=optimizer,
            lr0=learning_rate if learning_rate else 0.01, # lr0 is initial learning rate, ultralytics has defaults if None
            project=project_name,
            name=experiment_name,
            device=device,
            # Ultralytics' train function has many more parameters.
            # Add them here or in config.yaml's training section as needed.
            # e.g., patience, workers, pretrained, etc.
            # Augmentation parameters can also be passed if you want to override defaults.
            # See ultralytics docs for model.train() arguments.
        )
        print("\nTraining complete.")
        print(f"Trained model and results saved in: {project_name}/{experiment_name}")

        # The best model is usually saved as 'best.pt' in the experiment directory.
        # Update the main config's model.path to point to this new best model if desired.
        # This part can be manual or automated based on workflow.
        # For now, we just print the location.
        best_model_path = os.path.join(project_name, experiment_name, 'weights', 'best.pt')
        if os.path.exists(best_model_path):
            print(f"Best model saved at: {best_model_path}")
            print(f"Consider updating 'model.path' in '{cli_args.app_config}' to this path for future use.")
        else:
            print("Could not find 'best.pt'. Check training output for saved model paths.")

    except Exception as e:
        print(f"An error occurred during YOLO model training: {e}")
        # Potentially log the error or raise it
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train a YOLO Helmet Detection Model")

    # Required argument for dataset YAML
    parser.add_argument('--dataset_yaml', type=str, required=True,
                        help="Path to the dataset .yaml file (e.g., data/helmet_data.yaml). "
                             "This YAML file should define train/val image paths and class names.")

    # Optional arguments that can override app_config.yaml settings
    parser.add_argument('--app_config', type=str, default="config/config.yaml",
                        help="Path to the main application configuration file.")
    parser.add_argument('--model_path', type=str, default=None,
                        help="Path to an initial model (.pt or .yaml) to load for training (e.g., 'yolov8n.pt', 'path/to/custom.yaml'). Overrides config.")
    parser.add_argument('--epochs', type=int, default=None,
                        help="Number of training epochs. Overrides config.")
    parser.add_argument('--batch_size', type=int, default=None,
                        help="Training batch size. Overrides config.")
    parser.add_argument('--img_size', type=int, default=None,
                        help="Image size for training (e.g., 640). Overrides config.")
    parser.add_argument('--optimizer', type=str, default=None,
                        help="Optimizer to use (e.g., 'SGD', 'Adam', 'AdamW', 'auto'). Overrides config.")
    parser.add_argument('--lr', type=float, default=None,
                        help="Initial learning rate. Overrides config.")
    parser.add_argument('--device', type=str, default=None,
                        help="Device to train on (e.g., 'cpu', '0' for CUDA device 0, '0,1,2,3' for multiple GPUs). Default is auto-select.")
    parser.add_argument('--project_name', type=str, default=None,
                        help="Directory to save training runs (e.g., 'my_training_runs'). Default 'runs/train'.")
    parser.add_argument('--experiment_name', type=str, default=None,
                        help="Name for this specific training experiment (e.g., 'helmet_yolov8n_run1'). Default 'exp'.")

    args = parser.parse_args()

    try:
        app_config_data = load_app_config(args.app_config)

        # The dataset_yaml path in app_config.data.dataset_yaml can be a default
        # but CLI --dataset_yaml is required and takes precedence.
        if not os.path.exists(args.dataset_yaml):
             default_yaml_from_config = app_config_data.get('data',{}).get('dataset_yaml')
             if default_yaml_from_config and os.path.exists(default_yaml_from_config):
                 print(f"Warning: --dataset_yaml '{args.dataset_yaml}' not found. Using dataset_yaml from app_config: '{default_yaml_from_config}'")
                 args.dataset_yaml = default_yaml_from_config
             else:
                raise FileNotFoundError(f"Dataset YAML file not found at '{args.dataset_yaml}' and no valid fallback in app_config.")

        train_yolo_model(app_config=app_config_data,
                         dataset_yaml_path=args.dataset_yaml,
                         cli_args=args)

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # For debugging, you might want to re-raise e
        # raise
```
