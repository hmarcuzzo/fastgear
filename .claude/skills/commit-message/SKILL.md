---
name: commit-message
description: Write a commit message for this repository. Use whenever creating a git commit — covers the gitmoji header format, the body, the allowed footers and the reserved release header.
---

# Commit messages

## Header

```text
<emoji> <short summary>
```

- **`<emoji>`** — exactly one gitmoji from the table below, written as the emoji itself and not
  as its `:code:`, the way `.gitmojirc.json` is configured.
- **`<short summary>`** — imperative, present tense, starting with an uppercase letter, at most
  80 characters. Do not repeat what the emoji already says: with `♻️`, write
  `Extract validation helpers`, not `Refactor validation helpers`.

```text
✨ Add EnvBaseSettings and dotenv file handling fixtures
```

There is no scope and no issue reference; the header ends at the summary.

`🔖 Release version <x.y.z>` is reserved. `python-semantic-release` writes it, and CD greps for
exactly that wording to tag, publish to PyPI and cut the GitHub release — never write a release
commit by hand, and never start any other commit with `🔖`.

## Body (optional)

A short summary, never a write-up: **three or four lines at most**, separated from the header by
a blank line and wrapped at 100 characters. Say why the change was made, and only when the header
cannot say it alone. Most commits in this repository have no body at all.

What the diff already shows, how the change was verified, and the alternatives weighed do not
belong here. Put them in the pull request.

```text
♻️ Make SQLAlchemy-dependent symbols conditionally importable

Importing fastgear without the sqlalchemy extra raised ModuleNotFoundError instead of the
ImportError naming the extra to install.
```

## Footer (optional)

Only issue-closing keywords, breaking-change notices and co-author credits:

```text
Closes #24
BREAKING CHANGE: pagination options no longer accept a bare dict
```

Never add `Co-Authored-By: Claude` or `Claude-Session:` trailers. Messages in this repository end
at the body.

## Gitmoji

| Gitmoji | Code | Use for |
|:-------:|:-----|:--------|
| 🎨 | `:art:` | Improve structure / format of the code |
| ⚡️ | `:zap:` | Improve performance |
| 🔥 | `:fire:` | Remove code or files |
| 🐛 | `:bug:` | Fix a bug |
| 🚑️ | `:ambulance:` | Critical hotfix |
| ✨ | `:sparkles:` | Introduce new features |
| 📝 | `:memo:` | Add or update documentation |
| 🚀 | `:rocket:` | Deploy stuff |
| 💄 | `:lipstick:` | Add or update the UI and style files |
| 🎉 | `:tada:` | Begin a project |
| ✅ | `:white_check_mark:` | Add, update, or pass tests |
| 🔒️ | `:lock:` | Fix security or privacy issues |
| 🔐 | `:closed_lock_with_key:` | Add or update secrets |
| 🔖 | `:bookmark:` | Release / version tags |
| 🚨 | `:rotating_light:` | Fix compiler / linter warnings |
| 🚧 | `:construction:` | Work in progress |
| 💚 | `:green_heart:` | Fix CI build |
| ⬇️ | `:arrow_down:` | Downgrade dependencies |
| ⬆️ | `:arrow_up:` | Upgrade dependencies |
| 📌 | `:pushpin:` | Pin dependencies to specific versions |
| 👷 | `:construction_worker:` | Add or update CI build system |
| 📈 | `:chart_with_upwards_trend:` | Add or update analytics or track code |
| ♻️ | `:recycle:` | Refactor code |
| ➕ | `:heavy_plus_sign:` | Add a dependency |
| ➖ | `:heavy_minus_sign:` | Remove a dependency |
| 🔧 | `:wrench:` | Add or update configuration files |
| 🔨 | `:hammer:` | Add or update development scripts |
| 🌐 | `:globe_with_meridians:` | Internationalization and localization |
| ✏️ | `:pencil2:` | Fix typos |
| 💩 | `:poop:` | Write bad code that needs to be improved |
| ⏪️ | `:rewind:` | Revert changes |
| 🔀 | `:twisted_rightwards_arrows:` | Merge branches |
| 📦️ | `:package:` | Add or update compiled files or packages |
| 👽️ | `:alien:` | Update code due to external API changes |
| 🚚 | `:truck:` | Move or rename resources |
| 📄 | `:page_facing_up:` | Add or update license |
| 💥 | `:boom:` | Introduce breaking changes |
| 🍱 | `:bento:` | Add or update assets |
| ♿️ | `:wheelchair:` | Improve accessibility |
| 💡 | `:bulb:` | Add or update comments in source code |
| 💬 | `:speech_balloon:` | Add or update text and literals |
| 🗃️ | `:card_file_box:` | Perform database related changes |
| 🔊 | `:loud_sound:` | Add or update logs |
| 🔇 | `:mute:` | Remove logs |
| 👥 | `:busts_in_silhouette:` | Add or update contributors |
| 🚸 | `:children_crossing:` | Improve user experience / usability |
| 🏗️ | `:building_construction:` | Make architectural changes |
| 📱 | `:iphone:` | Work on responsive design |
| 🤡 | `:clown_face:` | Mock things |
| 🥚 | `:egg:` | Add or update an easter egg |
| 🙈 | `:see_no_evil:` | Add or update a .gitignore file |
| 📸 | `:camera_flash:` | Add or update snapshots |
| ⚗️ | `:alembic:` | Perform experiments |
| 🔍️ | `:mag:` | Improve SEO |
| 🏷️ | `:label:` | Add or update types |
| 🌱 | `:seedling:` | Add or update seed files |
| 🚩 | `:triangular_flag_on_post:` | Add, update, or remove feature flags |
| 🥅 | `:goal_net:` | Catch errors |
| 💫 | `:dizzy:` | Add or update animations and transitions |
| 🗑️ | `:wastebasket:` | Deprecate code that needs to be cleaned up |
| 🛂 | `:passport_control:` | Authorization, roles and permissions |
| 🩹 | `:adhesive_bandage:` | Simple fix for a non-critical issue |
| 🧐 | `:monocle_face:` | Data exploration / inspection |
| ⚰️ | `:coffin:` | Remove dead code |
| 🧪 | `:test_tube:` | Add a failing test |
| 👔 | `:necktie:` | Add or update business logic |
| 🩺 | `:stethoscope:` | Add or update healthcheck |
| 🧱 | `:bricks:` | Infrastructure related changes |
| 🧑‍💻 | `:technologist:` | Improve developer experience |
| 💸 | `:money_with_wings:` | Sponsorships or money related infrastructure |
| 🧵 | `:thread:` | Multithreading or concurrency |
| 🦺 | `:safety_vest:` | Validation |
| ✈️ | `:airplane:` | Improve offline support |

## Examples

```text
🐛 Handle null pointer on signup
📝 Add FastGear CLI section to README
♻️ Ensure options are only applied when values are present
✅ Add unit tests for token refresh
👷 Add timeout to deployment step in CI configuration
⬆️ Update dependencies to resolve security issues
```
