# Install Woodcore

Woodcore installs in a minute, without administrator rights, and holds everything a report needs: the program with its window, the `woodcore-cli` command line and Typst.

## Download and install

Download the installer from the [Download](~/download/) page and run it. As it is not signed, Windows may show «Windows protected your PC»: click **More info**, then **Run anyway**.

Leave **Open .woodcore files with Woodcore** ticked. A Woodcore project is a folder holding a file `<name>.woodcore`: with this option, a double-click on that file opens the project, the way a Word document opens in Word.

> [!tip]
> Woodcore installs for your user into `%LOCALAPPDATA%\Programs\Woodcore\<version>\`. Every version has its folder: a new version never replaces the old one.

## The tools beside it

Woodcore reads Excel workbooks and writes a report in Typst. Two tools make the work comfortable:

- **Microsoft Excel**, to fill in the load workbook;
- **Visual Studio Code** with the **Tinymist** extension, to write the report: Tinymist shows every command's documentation on hover and a live preview of the PDF.

Typst itself ships with Woodcore: there is nothing more to install.

## Staying up to date

At every start, Woodcore looks whether a newer version is published on this site. If one is, a window presents it with what is new and offers to install it: Woodcore downloads the installer, checks its fingerprint and runs it. The versions installed stay, and the Start menu opens the newest from then on.

In the next step we create a first project.
