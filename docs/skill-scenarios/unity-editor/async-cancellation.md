# Scenario: async-cancellation

**Prompt:** Show a 3 second countdown that stops if the popup closes.

**Expected:** UniTask.Delay with CancelToken.Token, cancel previous run, cancel in OnDisable.

**Must not:** Task.Run, or cache Token across Cancel().
