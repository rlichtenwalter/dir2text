The SIGPIPE test now closes a real pipe mid-output and checks the CLI's own exit status, so it fails if SIGPIPE handling breaks.
