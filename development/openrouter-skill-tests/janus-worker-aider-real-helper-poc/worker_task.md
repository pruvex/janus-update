You are acting as a bounded code worker inside an isolated temporary workspace.

Task:
- fix `lean_precheck_eval.py` so that the provided pytest test passes

Hard boundaries:
- edit only `lean_precheck_eval.py`
- do not modify `test_real_helper.py`
- do not create or modify any other file
- do not add unrelated refactors
- do not mention commits, pushes, branches, or releases

Goal:
- keep the fix tiny
- preserve existing helper behavior
- make the failing test pass

Definition of success:
- the pre-run test fails
- the post-run test passes
- only `lean_precheck_eval.py` changes
- no scope drift happens
