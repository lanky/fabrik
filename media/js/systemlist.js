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
*/

function getSystems() {
    // an attempt to fetch system info via AJAX and return it
    var systems = new Array();
    $.getJSON({ 
        url: '/apps/fabrik/ajax/list/allsystems',
        success: function(data) {
            for (i = 0; i < data.length; i++) {
                // reindex on name, for simplicity
                // (realistically I could have just returned the data this way, but...)
                systems[data[i].name] = data[i];
            }
        }
    return systems;
}
function systemToRow(jsondata, sysname) {
    var sysinfo = jsondata[sysname];
    // try adding a CSS/HTML id to the row, so we know which system this is...
    var start = '<tr id=' + sysname + '_row' + '><td>'
    var mid = '</td><td>'
    var end = '</td></tr>'
    var ifdata = '';
    for ( i=0; i < sysinfo.interfaces.length; i++ ) {
        ifdata += sysinfo.interfaces[i] + ':' + sysinfo.interfaces[i].ip_address
        if (i < sysinfo.interfaces.length - 1 ){
            ifdata += '<br/>'
            }
        }
    return start + sysname + mid + sysinfo.profile + mid + ifdata + end;
    
}
function fillTable(jsondata, tableid){
    // create tbody section based on the JSON system list
    // then convert it to a datatable.
    var htmlout = '';
    for (var sysname in jsondata) {
        htmlout += systemToRow(jsondata, sysname);
    }
    // set the html for the table body
    $('tbody', tableid).html(htmlout);
    // convert to a 'dataTable'
    $(tableid).dataTable();
}

function sysArray(jsondata) {
    /* returns an array for dataTables
    should have columns in rendering order
    */
    var sys_list = new Array();
    for ( var sysname in jsondata){
        var current = [ sysname, sysname.profile, sysname.interfaces[0].ip_address, sysname.comment ];
        sys_list.push(current);
    }
    return sys_list
}
$(function() {
    systems = getSystems();
    myrows = sysArray(systems)
    $('#listsystems').addClass('current');
    $('#systable').dataTable( {
        "bprocessing" : true,
        "sAjaxSource": "/apps/fabrik/ajax/test1",
        "aoColumns" : [
            { "sTitle" : "Name" },
            { "sTitle" : "Profile" },
            { "sTitle" : "IP Address" },
            { "sTitle" : "Comment" }
        ]

    });

}); // end doc ready
