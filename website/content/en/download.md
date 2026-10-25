# Download Woodcore

{{download}}

## Requirements

| Component | | Note |
|---|---|---|
| Windows 10 or 11, 64-bit | required | Woodcore is a Windows program. |
| About 250 MB per version | required | Every version is installed into a folder of its own. |
| Administrator rights | no | It installs for the user, into `%LOCALAPPDATA%\Programs\Woodcore\`. |
| Microsoft Excel and a load workbook | no | Wind, snow and permanent loads are entered in Woodcore's tabs, as the positions are. A `Belastungsannahmen` workbook is never opened. |
| Visual Studio Code with the Tinymist extension | recommended | To write the report, with every command's documentation on hover. |
| Typst | included | Typst 0.14.2 ships with Woodcore: nothing to install. |
| An Internet connection | optional | Only to learn whether a new version is published. |

## Install

1. Download the installer above and run it.
2. Windows may show «Windows protected your PC»: the installer is not signed. Click **More info**, then **Run anyway**.
3. Choose the wizard's language and leave **Open .woodcore files with Woodcore** ticked: a double-click on a project will open it.
4. At the end, Woodcore opens on its start page.

The Start menu holds **Woodcore**, which always opens the newest version installed, and one entry per version.

## Updates

At every start, Woodcore asks this site whether a new version is published. If one is, a window presents it with what is new:

- **Install** downloads the installer, checks its SHA-256 and runs it;
- **Later** asks again the next day;
- **Skip this version** does not offer it again — the next one will be.

Without a connection nothing is shown and nothing is slowed down.

## Several versions side by side

A new version installs **beside** the previous ones, never replacing them. A project exported years ago therefore opens again with the version that produced it: in **File › Project properties**, the **Woodcore version** field pins a project to a version. A double-click on a project opens the version it asks for, else the newest.

## Uninstall

Every version is uninstalled on its own, in Windows' **Settings › Apps**, under the name «Woodcore 0.89.0». Your projects are never touched: they live in their own folders.
