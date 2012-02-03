README for fabrik/templates directory
=====================================

This contains the HTML templates in use by fabrik interface
These could arguably be simplified a little.
The .tmpl extension is purely arbitrary - many examples use.html

The Templates
-------------

* main.tmpl
the global template inherited by the others.

### system record management
* system_add.tmpl
  create new system record
  Allows for all kinds of extra stuff, such as uploading snippets
  (specifically for disk layouts)

* systemsummary.tmpl
  summary form post-creation

* system_list.tmpl

* system_delete.tmpl
  choose a system to delete

* delete_confirm.tmpl
  do you really mean it?

* delete_result.tmpl
  did it work?

ISO image generation
--------------------
* iso_create.tmpl
  Pick a system(s) and or profile(s) to add to your ISO image.

* iso_summary.tmpl
  was the ISO successfully generated, plus a download link.



