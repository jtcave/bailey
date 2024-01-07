# bailey - key-value store, capable of storing Python programs

This is a key-value store inspired by the famous description of ["Barbara" from "Bank Python"](https://calpaterson.com/bank-python.html). In essence, it's a global namespace that remote clients can attach to. The client includes an import loader, so modules can be imported straight from bailey.

## Features

* Store any pickleable object
* Uses the filesystem as a backing store; all manner of hacks are possible
* Import from the store! Any string object under the `/py` superkey is importable!

## Non-goals

* Robustness, performance, or any sort of production readiness
* The "Dagger" and "MnTable" components from "Bank Python"
* The "in-house IDE"

## Deficiencies

* "Wapole" (the job server) isn't implemented
* Client/server transport is XML-RPC 🤢
* As implemented, remote access isn't enabled yet
* The import hook is a half-baked, barely tested hack, with no support for submodules or packages
    * Bytecode isn't cached, either
* This is a hack I threw together on a snow day
* Just like "Bank Python", you can't edit in-store code using regular editors

## How to use

Start a server:

```
$ mkdir /tmp/bailey
$ python -m bailey.server
```

Attach a client:

```python
from bailey import bailey
bailey()['/key/path'] = "value"
if bailey()['/key/path'] == "value":
    print("Success!")
```

### Importing from bailey

From one interpreter:

```python
from bailey import bailey
bailey()['/py/cool_math'] = """
def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n-1)
"""
```

And from another:

```python
from bailey import bailey
bailey()   # this installs the import hook
import cool_math
print(cool_math.factorial(5))   # 120
```
