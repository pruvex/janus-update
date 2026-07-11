# Delegated Result

Accepted proposal-first execution patch candidate normalized for write-apply validation.

```diff
--- a/backend/services/contact_manager.py
+++ b/backend/services/contact_manager.py
@@ -L +L @@
     if _should_auto_apply_contact_memory_update(
         memory=memory,
         match_mode=match_mode,
         metadata=metadata,
         proposal_payload=proposal_payload,
     ):
         return _apply_contact_memory_update_directly(
             db_session,
             target_contact=target_contact,
             proposal_payload=proposal_payload,
         )
+    else:
+        return {
+            "status": "proposed",
+            "reason": "requires_review",
+            "proposals_staged": 1,
+            "proposal_payload": proposal_payload,
+            "target_contact_id": target_contact.id,
+        }
```
