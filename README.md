# autoXLIFF
A tool to help developers manage their XLIFF translation files automatically from their Twig templates. It works out of box with Silex/Symphony and is flexible enough to work with other frameworks that are using Twig.

Pull requests welcome to improve this project !

If you don't #RTFM, please read the warnings at the bottom of this file !

## Description
autoXLIFF will scan your Twig templates looking for translation tokens. It will then update your project's XLIFF files accordingly, or create them for you if needed.

Not only will autoXLIFF add new tokens from your Twig templates to your translation files, it will also prune their old entries (those translation units in your XLIFF files that do not match any more tokens in your Twig templates).

Using autoXLIFF you will be able to automatically create XLIFF files for all translated strings in your projets and keep your Twig templates in sync with your XLIFF files.

## Usage
Scan your project's Twig templates and create or update your english translation file:
`autoXLIFF.py /path/to/project en.xlf`
if that file does not exist, this is equivalent as :
`autoXLIFF.py /path/to/project en.xlf --lang en/en`

Scan your project's Twig templates and create a translation file from english to french:
`autoXLIFF.py /path/to/project fr.xlf --lang en/fr`

Once files are created you can drop the --lang parameter. So to update that french localization file you just created, you can run:
`autoXLIFF.py /path/to/project fr.xlf`

Scan your project's Twig templates and see what changes would have been made to your XLIFF file, without actually changing anything :
`autoXLIFF.py /path/to/project fr.xlf --dry`

With the `--dry` flag, the program will display the number of translation tokens count and will show what translation units need to be added and/or removed to your XLIFF files in order to stay in sync. It's a safe way to actually test autoXLIFF.

## Options
By default autoXLIFF will look for Twig templates and XLIFF files in the default Silex directories (*views/* and *locales/*). 
This can be changed using the --locdir parameter (relative path to your project's locales directory) and --twigdir (relative path to your project's Twig templates)

As usual, `autoXLIFF -h` will display some help.

## Opinions
You might be wondering why the default language pair for creating new XLIFF files is en/en. This is because autoXLIFF works on the premises that your source language is actually translation tokens.
So that first en/en file will actually translate stuff like this :
* register.form.title = Create a new account 
* register.form.name = Last name

While your en/fr file will match the same stuff like this :
* register.form.title = Créer un nouveau compte 
* register.form.name = Nom

Of course, if you do not use translation tokens in your project that's fine. You won't need to create that initial en/en file and can go ahead creating your first international language file with `autoXLIFF.py /path/to/project fr.xlf`, for example. It'll show your original language strings in english all right.

## Twig syntax
Thanks to an massively ungodly regex, autoXLIFF is able to recognize the following Twig tags :
* {% trans %}register.new-account{% endtrans %}
* {{ 'register.new-account'|trans }}
* {{ app.translator.trans('register.new-account') }}
* {% trans with {'%name%': 'Jerome'} from "app" %}Hello %name%{% endtrans %}
* {% trans with {'%name%': 'Jerome'} %}Hello %name%{% endtrans %}
* {% Trans %}register.new-account{% endTRANS %}
* {% trans with {'%name%': 'Jerome'} %}Hello %name%{% endtrans %}
* {{ 'register.new-account%name%'|trans({'%name%': 'jerome'}) }}

white spaces and single or double are irrelevant, and the search is case insensitive. Also, the search within the Twig templates directory is recursive, so you don't need to worry about subfolders.

Please note that at this time autoXLIFF does not support *transchoice* tags.

## WARNING
autoXLIFF **WILL** overwrite your XLIFF files. Please take a second to read that again ;)

The intended use for this program is to start fresh from your web project and let it scan your Twig templates, so it can manage the XLIFF files it creates.

When working with existing XLIFF files autoXLIFF will usually import them alright. But after updating it will write back to that very same file and overwrite its body section with a much simpler XLIFF that what you're probably working with.

It will (should...) preserve the header and its content (*phase-group* blocks and such). But everything inside the \<body\> tag will be overwritten with a very basic trans-units grammar. It's fine, but it will not save your *maxbytes* and *xml:lang*, for example. Be warned !
As usual, make backup. This software is offered as is and I do not make any guarantee about its operation.

## Future versions
Depending on feedback, I might add support for :
- Transchoice syntax (I guess I'll add it once I need it)
- Kind of plugable regex to allow for easy adaptation to another framework syntax (just write the regex, put in in a file and autoXLIFF will load it instead of its default Silex/Symphony Twig bridge syntax. 

## What can I use to actually translate my project ?
autoXLIFF will create and manage XLIFF files automatically for you. Provided you run it regularly, it will keep their content in sync with your actual Twig templates content.
But it's still up to you to do the actual translation. To edit your files, you can use XLIFFTool by Remus Lazar (free, simple and does the job well) or a host of other commercial editors (Counterparts Light seems well appreciated)

* XLIFFTool : [http://remuslazar.github.io/osx-xliff-tool/][1]
* Counterparts Light : [https://michelf.ca/logiciels/counterparts-lite/][2]

[1]:	http://remuslazar.github.io/osx-xliff-tool/
[2]:	https://michelf.ca/logiciels/counterparts-lite/
