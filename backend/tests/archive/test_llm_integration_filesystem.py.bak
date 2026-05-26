import os
from unittest.mock import AsyncMock, patch

import pytest
from backend.data.schemas_tools import ToolResultV1
from backend.services.tool_manager import tool_manager
from backend.tool_registry import TOOL_REGISTRY, register_all_tools
from pyfakefs.fake_filesystem_unittest import Patcher


class TestLLMIntegrationFilesystem:
    @pytest.fixture(autouse=True)
    def setup_fake_filesystem(self):
        # FIX: Wir leeren das existierende Dictionary, statt es zu überschreiben.
        # So bleibt die Referenz von TOOL_REGISTRY gültig.
        if hasattr(tool_manager.tools, "clear"):
            tool_manager.tools.clear()
        else:
            # Fallback falls es kein Dict ist (sollte nicht passieren)
            tool_manager.tools = {}

        # Neu registrieren
        register_all_tools()

        # Fake Filesystem starten
        with Patcher():
            yield

    @property
    def default_workspace(self):
        return "C:/fake_app_data/workspace"

    def _ensure_workspace(self):
        if not os.path.exists(self.default_workspace):
            os.makedirs(self.default_workspace)

    @pytest.mark.asyncio
    async def test_llm_calls_create_file_tool(self, setup_fake_filesystem):
        self._ensure_workspace()
        file_path = f"{self.default_workspace}/llm_test.txt"

        mock_llm_response = {
            "type": "tool_code",
            "tool_name": "create_file",
            "tool_args": {"path": file_path, "content": "Hello World"},
            "usage": {},
            "cost": {},
        }

        with patch(
            "backend.services.llm_gateway.reason_and_respond", new_callable=AsyncMock
        ) as mock_r:
            mock_r.return_value = mock_llm_response

            tool_name = mock_llm_response["tool_name"]

            # Debugging: Falls dies fehlschlägt, zeigen wir, was drin ist
            assert tool_name in TOOL_REGISTRY, (
                f"Fehlt: {tool_name}. Vorhanden: {list(TOOL_REGISTRY.keys())}"
            )

            tool_func = TOOL_REGISTRY[tool_name].func
            result = tool_func(**mock_llm_response["tool_args"])

            assert isinstance(result, ToolResultV1)
            assert "erfolgreich erstellt" in (result.message or "")
            assert os.path.exists(file_path)
            with open(file_path, "r") as f:
                assert f.read() == "Hello World"

    @pytest.mark.asyncio
    async def test_llm_calls_read_file_tool(self, setup_fake_filesystem):
        self._ensure_workspace()
        file_path = f"{self.default_workspace}/read.txt"
        with open(file_path, "w") as f:
            f.write("Secret Content")

        # Direktzugriff auf Registry sicherstellen
        assert "read_file" in TOOL_REGISTRY
        tool_func = TOOL_REGISTRY["read_file"].func

        result = tool_func(path=file_path)
        assert isinstance(result, ToolResultV1)
        assert "Secret Content" in result.model_dump()["data"]["output"]

    @pytest.mark.asyncio
    async def test_llm_calls_delete_file_tool(self, setup_fake_filesystem):
        self._ensure_workspace()
        file_path = f"{self.default_workspace}/del.txt"
        with open(file_path, "w") as f:
            f.write("Bye")

        assert "delete_file" in TOOL_REGISTRY
        tool_func = TOOL_REGISTRY["delete_file"].func

        tool_func(path=file_path)
        assert not os.path.exists(file_path)

    @pytest.mark.asyncio
    async def test_llm_calls_create_directory_tool(self, setup_fake_filesystem):
        self._ensure_workspace()
        dir_path = f"{self.default_workspace}/new_folder"

        assert "create_directory" in TOOL_REGISTRY
        tool_func = TOOL_REGISTRY["create_directory"].func

        tool_func(path=dir_path)
        assert os.path.isdir(dir_path)

    @pytest.mark.asyncio
    async def test_llm_calls_list_directory_tool(self, setup_fake_filesystem):
        self._ensure_workspace()

        assert "list_directory" in TOOL_REGISTRY
        tool_func = TOOL_REGISTRY["list_directory"].func

        result = tool_func(path=self.default_workspace)
        assert isinstance(result, ToolResultV1)

    @pytest.mark.asyncio
    async def test_llm_calls_delete_directory_tool(self, setup_fake_filesystem):
        self._ensure_workspace()
        dir_path = f"{self.default_workspace}/del_dir"
        os.makedirs(dir_path)

        assert "delete_directory" in TOOL_REGISTRY
        tool_func = TOOL_REGISTRY["delete_directory"].func

        tool_func(path=dir_path)
        assert not os.path.exists(dir_path)

    @pytest.mark.asyncio
    async def test_llm_calls_move_file_tool(self, setup_fake_filesystem):
        self._ensure_workspace()
        src = f"{self.default_workspace}/src.txt"
        dst = f"{self.default_workspace}/dst.txt"
        with open(src, "w") as f:
            f.write("Moved")

        assert "move_file" in TOOL_REGISTRY
        tool_func = TOOL_REGISTRY["move_file"].func

        tool_func(source_path=src, destination_path=dst)
        assert not os.path.exists(src)
        assert os.path.exists(dst)

    @pytest.mark.asyncio
    async def test_llm_calls_rename_file_tool(self, setup_fake_filesystem):
        if "rename_file" not in TOOL_REGISTRY:
            pytest.skip("Tool 'rename_file' nicht in Registry.")

        self._ensure_workspace()
        old = f"{self.default_workspace}/old.txt"
        new = f"{self.default_workspace}/new.txt"
        with open(old, "w") as f:
            f.write("Renamed")

        tool_func = TOOL_REGISTRY["rename_file"].func
        tool_func(old_path=old, new_path=new)
        assert not os.path.exists(old)
        assert os.path.exists(new)

    @pytest.mark.asyncio
    async def test_llm_calls_move_files_tool(self, setup_fake_filesystem):
        self._ensure_workspace()
        src_dir = f"{self.default_workspace}/src_m"
        dst_dir = f"{self.default_workspace}/dst_m"
        os.makedirs(src_dir)
        with open(f"{src_dir}/a.txt", "w") as f:
            f.write("A")

        assert "move_files" in TOOL_REGISTRY
        tool_func = TOOL_REGISTRY["move_files"].func

        tool_func(source_directory=src_dir, destination_directory=dst_dir, pattern="*.txt")
        assert os.path.exists(f"{dst_dir}/a.txt")
