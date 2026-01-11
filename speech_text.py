import pickle
import numpy as np
from typing import List, Union
from glob import glob
from io import BytesIO
from pathlib import Path
from dataclasses import dataclass
import soundfile as sf
import tensorflow as tf
from tensorflow import keras
import librosa

from config import Config
from custom_logger import CustomLogger
from custom_decorators import timeit, log_call

logger = CustomLogger(logger_name="speech_text",
                      logger_log_level=Config.CLI_LOG_LEVEL,
                      file_handler_log_level=Config.FILE_LOG_LEVEL,
                      log_file_name=f"{Config.LOG_FOLDER}/speech_text.log"
                      ).create_logger()


@dataclass
class SpeechToText:
    model_folder: Union[str, Path]
    frame_length: int = Config.FRAME_LENGTH
    frame_step: int = Config.FRAME_STEP
    fft_length: int = Config.FFT_LENGTH

    @timeit(logger=logger)
    def __post_init__(self) -> None:
        try:
            model_path = glob(f"{self.model_folder}/*.h5")[0]
            self.model = keras.models.load_model(model_path, compile=False)

            with open(f"{self.model_folder}/num_to_char.pkl", "rb") as f:
                self.num_to_char = pickle.load(f)
        except Exception as e:
            logger.error(f"Unexpected error: {e} in init", exc_info=True)

    @log_call(logger=logger, log_params=[""], hide_res=True)
    @timeit(logger=logger)
    def load_and_process_audio(self, audio_input: Union[str, bytes, BytesIO], normalize: bool = False) -> np.ndarray:
        """reads audio and return spectrogram"""

        if normalize:
            audio = self.normalize_audio(audio_input)
        else:
            if isinstance(audio_input, bytes):
                audio, sample_rate = sf.read(BytesIO(audio_input))
            elif isinstance(audio_input, BytesIO):
                audio, sample_rate = sf.read(audio_input)
            else:
                # str - ścieżka do pliku
                audio, sample_rate = sf.read(audio_input)
        audio = audio.astype(np.float32)
        
        # Calculate spectrogram
        spectrogram = tf.signal.stft(
            audio, 
            frame_length=self.frame_length, 
            frame_step=self.frame_step, 
            fft_length=self.fft_length
        )
        spectrogram = tf.abs(spectrogram)
        spectrogram = tf.math.pow(spectrogram, 0.5)
        
        # Normalize
        means = tf.math.reduce_mean(spectrogram, axis=1, keepdims=True)
        stddevs = tf.math.reduce_std(spectrogram, axis=1, keepdims=True)
        spectrogram = (spectrogram - means) / (stddevs + 1e-10)
        
        return spectrogram.numpy()

    @log_call(logger=logger, log_params=[""], hide_res=False)
    @timeit(logger=logger)
    def decode_prediction(self, pred: np.ndarray) -> str:
        input_len = np.array([pred.shape[0]])
        
        # CTC decode
        results = keras.backend.ctc_decode(
            np.expand_dims(pred, 0), 
            input_length=input_len, 
            greedy=True
        )[0][0]
        
        # Filter out (-1) tokens
        result = results[0]
        result = tf.boolean_mask(result, result != -1)
        
        # Convert to text
        text = tf.strings.reduce_join(self.num_to_char(result)).numpy().decode("utf-8")

        return text
    
    @log_call(logger=logger, log_params=[""], hide_res=False)
    @timeit(logger=logger)
    def transcribe(self, audio_input: List[Union[str, bytes, BytesIO]], normalize: bool = False) -> str:
        # Get spectrograms
        spectrograms = []
        for audio_in in audio_input:
            spectrograms.append(self.load_and_process_audio(
                audio_input=audio_in,
                normalize=normalize)
            )
        
        # Padding
        max_len = max(s.shape[0] for s in spectrograms)
        freq_bins = spectrograms[0].shape[1]
        
        padded = np.zeros((len(spectrograms), max_len, freq_bins), dtype=np.float32)
        for i, spec in enumerate(spectrograms):
            padded[i, :spec.shape[0], :] = spec
        
        # Predykcja
        predictions = self.model.predict(padded, verbose=0)
        
        # Dekoduj
        text_list = []
        for pred in predictions:
            text_list.append(self.decode_prediction(pred))
        return text_list
    
    def normalize_audio(self, audio_input: Union[str, bytes, BytesIO], target_sample_rate: int = 16000) -> np.ndarray:
        if isinstance(audio_input, bytes):
            audio_input = BytesIO(audio_input)
        
        audio, sr = librosa.load(audio_input, sr=target_sample_rate, mono=True) 
        return audio.astype(np.float32)


if __name__ == "__main__":
    speech_to_text = SpeechToText(
        model_folder=Config.MODEL_FOLDER
    )

    # Transkrybuj plik
    audio_file = f"{Config.AUDIO_FILES_FOLDER}/1462-170145-0002.flac"
    audio_file2 = f"{Config.AUDIO_FILES_FOLDER}/422-122949-0000.flac"
    audio_file3 = f"{Config.AUDIO_FILES_FOLDER}/1272-128104-0009.flac"
    audio_file4 = f"{Config.AUDIO_FILES_FOLDER}/1272-135031-0009.flac"
    audio_file5 = f"{Config.AUDIO_FILES_FOLDER}/1462-170145-0002.flac"
    # print(f"Transkrypcja: {audio_file}")
    
    text = speech_to_text.transcribe([audio_file, audio_file2, audio_file3, audio_file4, audio_file5])

    print(f"Wynik: {text}")
