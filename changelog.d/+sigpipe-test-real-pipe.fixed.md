The SIGPIPE test now closes a real pipe mid-output and checks the CLI's own exit status with no timing sleep, so it fails if SIGPIPE handling breaks.
