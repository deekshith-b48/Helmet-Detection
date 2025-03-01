# 🪖 Helmet Detection

Welcome to the Helmet Detection project! This project aims to develop a computer vision model that can detect whether a person is wearing a helmet or not. This can be particularly useful in ensuring safety standards in various industries and scenarios such as construction sites, bike riding, and more.

## 🚀 Features

- **Real-time detection**: Detect helmets in real-time using a webcam or video feed.
- **High accuracy**: Utilizes advanced machine learning algorithms for high accuracy.
- **Easy integration**: Can be easily integrated into existing systems and applications.

## 🛠️ Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/deekshith-b48/Helmet-Detection.git
    cd Helmet-Detection
    ```

2. **Install the required dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## 🏃‍♂️ Usage

1. **Run the detection script**:
    ```bash
    python detect_helmet.py
    ```

2. **Using a webcam**:
    By default, the script will use the webcam for real-time detection. Ensure your webcam is connected and working.

3. **Using a video file**:
    To use a video file instead of a webcam, modify the script as follows:
    ```python
    video_path = 'path_to_your_video_file.mp4'
    cap = cv2.VideoCapture(video_path)
    ```

## 📊 Model Training

If you wish to train the model yourself, follow these steps:

1. **Prepare the dataset**:
    - Ensure you have a labeled dataset with images of people wearing helmets and not wearing helmets.

2. **Train the model**:
    ```bash
    python train_model.py
    ```

3. **Evaluate the model**:
    ```bash
    python evaluate_model.py
    ```

## 🤝 Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, feel free to open an issue or submit a pull request.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## 📞 Contact

For any inquiries, please reach out to [deekshith-b48](https://github.com/deekshith-b48).

Happy detecting! 🎉
