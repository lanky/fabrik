/*
# Fabrik - a custom django/javascript frontend to cobbler
#
# Copyright 2009-2012 Stuart Sears
#
# This file is part of fabrik
#
# fabrik is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# fabrik is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with fabrik. If not, see http://www.gnu.org/licenses/.

############################################################################################
#
# Functions used in the fabrik interface.
# mostly imported in the main.tmpl template
# They ALL rely on the availability of 
# 1. jquery-1.4.2
# 2. jquery-json
# plus maybe others as time goes on.
#
############################################################################################
*/

// use an AJAX call to resolve an IP -> hostname
function lookupIP(fqdn) {
    $.ajax({
        url: '/apps/fabrik/ajax/resolve/' + fqdn,
        success: function(response) {
            $('#id_ip_address').val(response);
        }
    });
}

// fetch file content via AJAX and fill a textarea with it.
function fetchFile(url, name, targetid) {
    $.ajax({
        url: url + '/' + name,
        success: function(response) {
            $(targetid).text(response)
        }
    });
}

// ajax function for setting select content from JSON
function setSelect(selectid, jsondata){
    var options = '';
    for (var i = 0; i < jsondata.length; i++) {
        options += '<option value="' + jsondata[i].val + '">' + jsondata[i].name + '</option>';
    }
    // set the select content based on ID
    $(selectid).html(options);
}

// populate a select using a JSON lookup, returning a JSON hash with 'name' and 'val' keys.
// combination of the 2 previous functions
// arguably more efficient.
function populateSelect(url, selectid){
    var options = '';
    $.getJSON(url, function(data) {
        for ( var i = 0; i < data.length; i++) {
        options += '<option value="' + data[i].val + '">' + data[i].name + '</option>';
        }
    $(selectid).html(options)
    });
}

// file layout saving moved into here from the main add system page
function saveLayout(layoutinfo) {
    // expects to be given JSON data (use $.toJSON) like this:
    // { 'name': filename, 'layout': filecontent}
    $.ajax({
            url: '/apps/fabrik/ajax/layouts/save',
            type: 'POST',
            contentType: 'application/json',
            data: layoutinfo,
            success: function(result) {
                alert(result);
            }
           });
}

// not used at the moment, but kept just in case...
function autocompleteList(url) {
    var entries = new Array();
    $.getJSON(url , function(data) {
                for ( var i=0; i < data.length; i++ ){
                entries += data[i].name;
              }
    return entries;
    });
}
// globally disable Enter in a TextInput, to avoid accidental form submission
// useful keycodes: Enter/Return : 9, Tab : 13
function disableEnterKey(){
  $('input').bind("keypress", function(e){
        if ( e.keyCode == 13) {
            return false;
        }
        });

}
// field toggling functionality
// enable list of (presumably disabled) fields if the 'toggleid' checkbox is ticked.
function enableFields(toggleid, fieldlist) {
    if ($(toggleid).is(':checked')) {
        for ( i=0; i < fieldlist.length; i++){
            $(fieldlist[i]).removeAttr('disabled');
            }
        }
    else {
        for ( i=0; i < fieldlist.length; i++){
            $(fieldlist[i]).attr('disabled', true);
        }
    }
};

// disable list of (presumably enabled) fields if the 'toggleid' checkbox is ticked.
function disableFields(toggleid, fieldlist) {
    if ($(toggleid).is(':checked')) {
        for ( i=0; i < fieldlist.length; i++){
            $(fieldlist[i]).attr('disabled', true);
            }
        }
    else {
        for ( i=0; i < fieldlist.length; i++){
        $(fieldlist[i]).removeAttr('disabled');
        }
    }
};
// post JSON to the delete systems URL
function delSystem(sysname){
    if (confirm ("really delete system " + sysname + "?")) {
        var jdata = $.toJSON({'systemname' : sysname});
        $.ajax({
                url: '/apps/fabrik/ajax/systems/delete',
                type: 'POST',
                data: jdata,
                success: function(result) {
                    alert("system deleted");
                }
               }); 
        alert("reload the page to refresh the system list")
        } 
}

// post JSON data for renaming...
function renameSystem(sysname){
    var newname = prompt('Enter a new System Name', sysname);
    var jdata = $.toJSON({'systemname' : sysname, 'newname' : newname});
    $.ajax({
           url: '/apps/fabrik/ajax/systems/rename',
           type: 'POST',
           contentType: 'application/json',
           data: jdata,
           success: function(result) {
              alert(result);
              }
           });
    }
// creates a cobbler profile from the given system    
function makeProfile(sysname){
    var profilename = prompt('Enter a name for the profile. No spaces.', sysname + '-profile');
    var jdata = $.toJSON({ 'profilename' : profilename, 'systemname' : sysname });
    $.ajax({
        url: '/apps/fabrik/ajax/systems/convert',
        type: 'POST',
        contentType: 'application/json',
        data: jdata,
        success: function(result) {
            alert(result);
            }
    });
}

/* because AJAX is, well, asynchronous, I can't just call the populateSelect 
function used in the other pages , as the jquery select modifications take place
before the AJAX call completes...
The solution:
include the bsmselect setrup in the populate function, as below:
*/
function populateBSMSelect(url, selectid){
    var options = '';
    $.getJSON(url, function(data) {
        for ( var i = 0; i < data.length; i++) {
        options += '<option value="' + data[i].val + '">' + data[i].name + '</option>';
        }
    $(selectid).html(options);
    // now, we've populated the select, so try converting it into a bsmselect...
    $(selectid).bsmSelect({
        addItemTarget: 'bottom',
        animate: true,
        highlight: true,
        plugins: [
            $.bsmSelect.plugins.sortable({ axis : 'y', opacity: '0.5'}, { listSortableClass : 'bsmListSortableCustom' }),
            $.bsmSelect.plugins.compatibility()
            ]
        });
    });
}    
