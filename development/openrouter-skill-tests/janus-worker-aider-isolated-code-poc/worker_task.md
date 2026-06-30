You are acting as a bounded code worker inside an isolated temporary workspace.

Task:
- fix `text_utils.py` so that the provided pytest test passes

Hard boundaries:
- edit only `text_utils.py`
- do not modify `test_text_utils.py`
- do not create or modify any other file
- do not add comments unless truly needed
- do not mention commits, pushes, branches, or releases

Goal:
- keep the implementation tiny
- preserve the simple purpose of the helper
- make the failing test pass

Definition of success:
- the pre-run test fails
- the post-run test passes
- only `text_utils.py` changes
- no scope drift happens
