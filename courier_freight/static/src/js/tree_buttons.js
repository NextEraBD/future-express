odoo.define('button_near_create.tree_button', function (require) {
"use strict";
var ListController = require('web.ListController');
var ListView = require('web.ListView');
var core = require('web.core');
var rpc = require('web.rpc');
var viewRegistry = require('web.view_registry');
var AbsentTreeButton = ListController.extend({
   buttons_template: 'courier_freight.buttons',
   events: _.extend({}, ListController.prototype.events, {
       'click .open_wizared': '_reload',
   }),
   _reload: function () {
        console.log('START open_wizared')
        var self = this;
        return rpc.query({
            model: 'freight.operation',
            method: 'action_open_operation_wizard',
            args: [],
        }, {
            shadow: true,
        }).then(function (result) {
            console.log('result',result)
            console.log('This',this)
            console.log('Self',self)
                self.reload();
                console.log('END open_wizared,Reloading')
        });

   }
});
var AbsentEmployeeListView = ListView.extend({
   config: _.extend({}, ListView.prototype.config, {
       Controller: AbsentTreeButton,
   }),
});
viewRegistry.add('button_get_absent', AbsentEmployeeListView);
});