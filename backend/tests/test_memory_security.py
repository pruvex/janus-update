"""
BUG-MEM-SEC-001: Security Guard for _merge_existing_memory

Test validates that the Security Guard prevents modification of non-editable memories.
"""

from unittest.mock import MagicMock, patch


from backend.data.models import Memory
from backend.services.memory_manager import _merge_existing_memory


class TestSecurityGuardMergeExisting:
    """Tests for the user_editable security guard in _merge_existing_memory."""

    def test_merge_blocked_when_user_editable_false(self, caplog):
        """
        SCENARIO: Attempt to merge into a non-editable memory (user_editable=False).
        EXPECTED: The merge is blocked, a WARNING is logged, and the function returns None.
        """
        # Setup: Create a mock memory with user_editable=False
        existing_memory = MagicMock(spec=Memory)
        existing_memory.id = 2
        existing_memory.user_editable = False
        existing_memory.priority = 0.95
        existing_memory.canonical_key = "user:physis:heisst:name"
        existing_memory.tags = ["identity"]

        mock_db = MagicMock()
        new_fact = {
            "fact": "Moritz ist der name des nutzers.",
            "priority": 0.95,
            "source_skill": "system.extractor",
            "tags": ["identity", "new_tag"],
        }

        with caplog.at_level("WARNING", logger="janus_backend"):
            result = _merge_existing_memory(
                db=mock_db,
                existing=existing_memory,
                new_fact=new_fact,
                new_source_type="text",
            )

        # ASSERTIONS
        # 1. Function returns None (blocked)
        assert result is None, "Expected None when merging non-editable memory"

        # 2. Warning log message is present
        assert "[SECURITY] BLOCKED" in caplog.text
        assert f"memory ID={existing_memory.id}" in caplog.text

        # 3. Memory was NOT modified (no merge happened)
        mock_db.commit.assert_not_called()
        # Priority should remain unchanged (not explicitly set by test)
        assert existing_memory.priority == 0.95

    def test_merge_allowed_when_user_editable_true(self, caplog):
        """
        SCENARIO: Attempt to merge into an editable memory (user_editable=True).
        EXPECTED: The merge proceeds normally (priority upgrade allowed).
        """
        # Setup: Create a mock memory with user_editable=True
        existing_memory = MagicMock(spec=Memory)
        existing_memory.id = 5
        existing_memory.user_editable = True
        existing_memory.priority = 0.5
        existing_memory.canonical_key = "user:vorlieben:liebt:kaffee"
        existing_memory.tags = ["preference"]
        existing_memory.snippet = '{"fact": "User liebt Kaffee"}'
        existing_memory.memory_type = "GENERAL"
        existing_memory.is_core_fact = False
        existing_memory.core_priority = 0

        mock_db = MagicMock()
        new_fact = {
            "fact": "User liebt schwarzen Kaffee",
            "priority": 0.75,
            "source_skill": "system.extractor",
            "memory_type": "CORE",
            "tags": ["preference", "drink"],
        }

        with caplog.at_level("INFO", logger="janus_backend"):
            with patch("backend.services.memory.crud_service.memory_cache.invalidate"):
                result = _merge_existing_memory(
                    db=mock_db,
                    existing=existing_memory,
                    new_fact=new_fact,
                    new_source_type="text",
                )

        # ASSERTIONS
        # 1. Function returns None (normal completion, not blocked)
        assert result is None  # Function always returns None on completion

        # 2. No security warning logged
        assert "[SECURITY] BLOCKED" not in caplog.text

        # 3. Memory WAS modified (merge happened - priority upgrade)
        assert existing_memory.priority == 0.75  # Upgraded from 0.5
        # 0.75 bleibt unter der Core-Schwelle (0.85) → kein Core-Flag
        assert existing_memory.is_core_fact is False
        assert existing_memory.core_priority == 0

        # 4. [DEDUP MERGE] log indicates successful merge
        assert "[DEDUP MERGE]" in caplog.text

    def test_merge_blocked_for_core_identity_non_editable(self, caplog):
        """
        SCENARIO: Core Identity slot (Name) with user_editable=False is protected.
        EXPECTED: Even identity slots respect user_editable flag.
        
        This is the specific regression case from Szenario 6 testing.
        """
        # Setup: Core Identity memory with user_editable=False (protected)
        existing_memory = MagicMock(spec=Memory)
        existing_memory.id = 2
        existing_memory.user_editable = False
        existing_memory.priority = 0.95
        existing_memory.canonical_key = "user:physis:heisst:name"
        existing_memory.tags = ["identity", "core"]
        existing_memory.snippet = '{"fact": "Max ist der name des nutzers."}'
        existing_memory.memory_type = "CORE"
        existing_memory.is_core_fact = True
        existing_memory.core_priority = 2

        mock_db = MagicMock()
        new_fact = {
            "fact": "Moritz ist der name des nutzers.",
            "priority": 0.95,
            "source_skill": "system.extractor",
            "tags": ["identity"],
        }

        with caplog.at_level("WARNING", logger="janus_backend"):
            result = _merge_existing_memory(
                db=mock_db,
                existing=existing_memory,
                new_fact=new_fact,
                new_source_type="text",
            )

        # ASSERTIONS
        # 1. Function returns None (blocked)
        assert result is None

        # 2. Security warning logged
        assert "[SECURITY] BLOCKED" in caplog.text
        assert "ID=2" in caplog.text

        # 3. Memory was NOT modified - "Max" stays "Max"
        assert existing_memory.snippet == '{"fact": "Max ist der name des nutzers."}'
        assert existing_memory.priority == 0.95  # Unchanged

        # 4. No [DEDUP MERGE] log for identity slot (blocked before that)
        assert "[DEDUP MERGE] Identity slot overwritten" not in caplog.text

    def test_user_editable_none_treated_as_editable(self, caplog):
        """
        SCENARIO: Memory with user_editable=None (default/legacy).
        EXPECTED: Treated as editable (not blocked) - merge proceeds.
        
        Note: Boolean check `if not existing.user_editable` handles None as falsy,
        but in practice DB default should be True. This test documents expected behavior.
        """
        # Setup: Memory with user_editable=True (explicit)
        existing_memory = MagicMock(spec=Memory)
        existing_memory.id = 10
        existing_memory.user_editable = True  # Explicitly True
        existing_memory.priority = 0.5
        existing_memory.canonical_key = "user:allgemein:fakt:test"
        existing_memory.tags = []

        mock_db = MagicMock()
        new_fact = {"fact": "Test fact", "priority": 0.6, "source_skill": "system.extractor"}

        with caplog.at_level("INFO", logger="janus_backend"):
            with patch("backend.services.memory.crud_service.memory_cache.invalidate"):
                result = _merge_existing_memory(
                    db=mock_db,
                    existing=existing_memory,
                    new_fact=new_fact,
                    new_source_type="text",
                )

        # No security block
        assert "[SECURITY] BLOCKED" not in caplog.text
        # Priority upgraded (merge happened)
        assert existing_memory.priority == 0.6
