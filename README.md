# Maya Toggl

Toggl time tracker in Maya

## Setup

1. Put the path to the `plugin` folder in your `MAYA_PLUG_IN_PATH`.
2. Put the path of this repository in your `PYTHONPATH`.
3. Put your api token in `TOGGL_TOKEN`.
4. Load plugin through the plugins menu in Maya.

### MacOS

`/Users/{user}/Library/Preferences/Autodesk/maya/{version}/Maya.env`

### Windows
`C:\Users\{user}\Documents\maya\{version}\Maya.env`

### Example Maya.env
```environment
PYTHONPATH=/path/to/repository
MAYA_PLUG_IN_PATH=/path/to/repository/plugin
TOGGL_TOKEN=12abcd34ef56gh7ij8k91l2mn3o456p7
```