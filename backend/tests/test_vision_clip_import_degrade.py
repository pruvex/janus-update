import unittest
from unittest.mock import MagicMock, patch

from backend.services.vision import model_loader
from backend.services import vision_service


class VisionClipImportDegradeTests(unittest.TestCase):
    def test_model_loader_marks_error_when_clip_import_is_unavailable(self):
        with patch.object(model_loader, "clip", None), patch.object(
            model_loader, "_CLIP_IMPORT_ERROR", RuntimeError("torchvision import failed")
        ):
            loader = model_loader.ClipModelLoader()

            self.assertEqual(loader.state, model_loader.ModelLoadingState.MODEL_ERROR)
            self.assertIn("clip import failed", str(loader.error_message))

            loader.start_async_load()

            self.assertIsNone(loader.model)
            self.assertIsNone(loader.preprocess)
            self.assertEqual(loader.state, model_loader.ModelLoadingState.MODEL_ERROR)

    def test_vision_service_process_image_returns_safe_result_when_clip_import_is_unavailable(self):
        service = vision_service.LocalVisionService()

        with patch.object(vision_service, "clip", None), patch.object(
            vision_service, "_CLIP_IMPORT_ERROR", RuntimeError("torchvision import failed")
        ), patch.object(vision_service.cv2, "imdecode", return_value=None):
            result = service.process_image(b"not-a-real-image", db=MagicMock(), profile=None, image_name="dummy.png")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["found_faces"], False)
        self.assertEqual(result["identified_names"], [])
        self.assertEqual(result["unknown_encodings"], [])


if __name__ == "__main__":
    unittest.main()
