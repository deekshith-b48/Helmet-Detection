import argparse
import yaml
import os
from ultralytics import YOLO

def load_app_config(config_path="config/config.yaml"):
    """Loads the main application configuration file."""
    if not os.path.exists(config_path):
        # Try to provide a more helpful message if it's the default path
        if config_path == "config/config.yaml":
            print(f"Warning: Default configuration file '{config_path}' not found. Evaluation might use default YOLO settings.")
            return {} # Return empty dict, let downstream handle defaults
        else:
            raise FileNotFoundError(f"Main configuration file not found: {config_path}")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def evaluate_yolo_model(app_config, dataset_yaml_path, model_path, cli_args):
    """
    Evaluates a trained YOLO model using the ultralytics library.

    Args:
        app_config (dict): The main application configuration.
        dataset_yaml_path (str): Path to the dataset's .yaml file (YOLO format for val/test set).
        model_path (str): Path to the trained .pt model file to evaluate.
        cli_args (argparse.Namespace): Command-line arguments.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not os.path.exists(dataset_yaml_path):
        raise FileNotFoundError(f"Dataset YAML file not found: {dataset_yaml_path}")

    print(f"Attempting to load model for evaluation: {model_path}")
    try:
        model = YOLO(model_path)
        print(f"Successfully loaded model: {model_path}")
    except Exception as e:
        print(f"Error loading model {model_path}: {e}")
        raise

    # Parameters for evaluation from CLI or app_config
    # Ultralytics' val mode uses many of the same params as predict (conf, iou) and train (imgsz)
    model_app_config = app_config.get('model', {})
    training_app_config = app_config.get('training', {}) # imgsz might be here

    imgsz = cli_args.img_size if cli_args.img_size is not None else model_app_config.get('imgsz', training_app_config.get('imgsz', 640))
    batch_size = cli_args.batch_size if cli_args.batch_size is not None else training_app_config.get('batch_size', 16) # val uses batch size too
    conf_thres = cli_args.conf_thres if cli_args.conf_thres is not None else model_app_config.get('confidence_threshold', 0.25) # Default from ultralytics is 0.25 for val
    iou_thres = cli_args.iou_thres if cli_args.iou_thres is not None else model_app_config.get('iou_threshold', 0.6) # Default from ultralytics is 0.6 for val
    device = cli_args.device if cli_args.device else '' # '' for auto-select
    split = cli_args.split if cli_args.split else 'val' # Dataset split to use ('val' or 'test')
    project_name = cli_args.project_name if cli_args.project_name else "runs/val"
    experiment_name = cli_args.experiment_name if cli_args.experiment_name else "exp"


    print("\n--- Evaluation Configuration ---")
    print(f"  Model: {model_path}")
    print(f"  Dataset YAML: {dataset_yaml_path}")
    print(f"  Dataset Split: {split}")
    print(f"  Image Size: {imgsz}")
    print(f"  Batch Size: {batch_size}")
    print(f"  Confidence Threshold: {conf_thres}")
    print(f"  IoU Threshold: {iou_thres}")
    print(f"  Device: {'Auto-select' if not device else device}")
    print(f"  Project Directory: {project_name}")
    print(f"  Experiment Name: {experiment_name}")
    print("------------------------------\n")

    try:
        # The `val` method in ultralytics YOLO class runs evaluation.
        # It returns a metrics object.
        metrics = model.val(
            data=dataset_yaml_path,
            imgsz=imgsz,
            batch=batch_size,
            conf=conf_thres,
            iou=iou_thres,
            split=split, # 'val', 'test', or 'train' (though 'train' is unusual for val)
            device=device,
            project=project_name,
            name=experiment_name,
            # Other args: save_json (for COCO eval), save_hybrid (labels + preds), etc.
        )

        print("\nEvaluation complete.")
        print(f"Metrics results saved in: {project_name}/{experiment_name}")

        # Ultralytics version 8.0.metrics.Metrics object has attributes like:
        # results_dict: A dictionary of all metrics
        # speed: A dictionary of speed metrics (preprocess, inference, postprocess)
        # maps: A list of mAP50-95 values per class (if applicable)
        # ap50: A list of AP50 values per class

        print("\n--- Key Metrics ---")
        if hasattr(metrics, 'results_dict'):
            for k, v in metrics.results_dict.items():
                print(f"  {k}: {v}")
        else:
            # Older ultralytics versions might store metrics differently or print them directly.
            # For recent versions, metrics object itself can be printed.
            print(metrics)

        # Example of accessing specific metrics (adjust based on ultralytics version and output)
        # map50_95 = metrics.results_dict.get('metrics/mAP50-95(B)', 0) # Box mAP
        # map50 = metrics.results_dict.get('metrics/mAP50(B)', 0)
        # print(f"  mAP50-95 (Box): {map50_95:.4f}")
        # print(f"  mAP50 (Box): {map50:.4f}")

    except Exception as e:
        print(f"An error occurred during YOLO model evaluation: {e}")
        # Potentially log the error or raise it
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate a trained YOLO Helmet Detection Model")

    parser.add_argument('--model_path', type=str, required=True,
                        help="Path to the trained .pt model file for evaluation.")
    parser.add_argument('--dataset_yaml', type=str, required=True,
                        help="Path to the dataset .yaml file (e.g., data/helmet_data.yaml). "
                             "This YAML should define val/test image paths and class names.")

    parser.add_argument('--app_config', type=str, default="config/config.yaml",
                        help="Path to the main application configuration file.")
    parser.add_argument('--img_size', type=int, default=None,
                        help="Image size for evaluation (e.g., 640). Overrides config.")
    parser.add_argument('--batch_size', type=int, default=None,
                        help="Evaluation batch size. Overrides config.")
    parser.add_argument('--conf_thres', type=float, default=None,
                        help="Confidence threshold for predictions during NMS. Overrides config.")
    parser.add_argument('--iou_thres', type=float, default=None,
                        help="IoU threshold for NMS. Overrides config.")
    parser.add_argument('--device', type=str, default=None,
                        help="Device to evaluate on (e.g., 'cpu', '0'). Default is auto-select.")
    parser.add_argument('--split', type=str, default='val', choices=['val', 'test', 'train'],
                        help="Dataset split to use for evaluation ('val', 'test', or 'train'). Default is 'val'.")
    parser.add_argument('--project_name', type=str, default=None,
                        help="Directory to save evaluation runs (e.g., 'my_eval_runs'). Default 'runs/val'.")
    parser.add_argument('--experiment_name', type=str, default=None,
                        help="Name for this specific evaluation experiment. Default 'exp'.")

    args = parser.parse_args()

    try:
        app_config_data = load_app_config(args.app_config)

        # Resolve dataset_yaml: CLI > app_config > error
        if not os.path.exists(args.dataset_yaml):
             default_yaml_from_config = app_config_data.get('data',{}).get('dataset_yaml')
             if default_yaml_from_config and os.path.exists(default_yaml_from_config):
                 print(f"Warning: --dataset_yaml '{args.dataset_yaml}' not found. Using dataset_yaml from app_config: '{default_yaml_from_config}'")
                 args.dataset_yaml = default_yaml_from_config
             else:
                raise FileNotFoundError(f"Dataset YAML file not found at '{args.dataset_yaml}' and no valid fallback in app_config.")

        evaluate_yolo_model(app_config=app_config_data,
                            dataset_yaml_path=args.dataset_yaml,
                            model_path=args.model_path,
                            cli_args=args)

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # For debugging, re-raise e
        # raise
```
