# Brownie

Learn by doing how to build browser engine by read [Browser Engineering](https://browser.engineering) book.

REMINDER: This repo is not for how to make sophisticated browser engine. Instead, it teach us how browser engine is designed.

> Note: Started from Chapter 8: Sending Information to Servers - Submitting Forms, I move all classes from lab08.py into dedicated classes in order to be able follow the next chapters.

## Why I create this repo?

The Browser Engineering book doesn't have a "diff" code in each section.

```diff
- This line has been removed.
+ This line has been added.
```

You can read the "diff" code by browse the commit in this repo.

## How to run?

> NOTE: This project use `uv`, an extremely fast Python package and project manager. Please visit [`uv` installation doc](https://docs.astral.sh/uv/getting-started/installation/).

```sh
uv run main.py https://browser.engineering
```

In chapter 8, you need run two commands: First command for the server. Second command for the browser engine.

```sh
uv run server/server8.py # This will run localhost:8080
uv run main.py http://localhost:8080 # server site
```

In chapter 9, you need run two commands: First command for the server. Second command for the browser engine.

```sh
uv run server/server9.py # This will run localhost:8080
uv run main.py http://localhost:8080 # server site
```
