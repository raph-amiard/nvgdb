nvgdb
=====

Nvgdb is yet-another graphical front-end for GDB. I whipped it together after
using [cgdb](https://cgdb.github.io/) for many years and growing frustrated
with it (it's still great software, you should check it out !).

why
---

I needed a front-end that had the following qualities:

1. Show me the code that I'm running (this is the basic thing that I used cgdb
   for).

2. Syntax highlighting for every language under the sun, and for ones not yet
   created via syntax files. cgdb fell short there.

3. Interact well with the regular gdb command line:
  * If I have a colored prompt, show me a colored prompt !
  * Handle utf-8 god damn it !

4. Be extensible. For example I use nvgdb to provide a custom debugger view for
   the [langkit project](https://github.com/langkit). Which allows a great
   debugging experience.

Of course, nvgdb achieves all that by being quite a bit heavier than cgdb,
since it relies on neovim and python. If you really want a lightweight
front-end, cgdb is still better.

non-goals
---------

Hiding gdb is not a goal, nor is providing mouse support. So it is expected
your primary interface to the debugger will be the command-line.

So, for the moment there is no way to:

1. Set break points visually (in development)
2. Navigate the stack-trace visually (planned)

And there will never be a way to click a button to do something.
