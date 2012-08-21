define(["Backbone","underscore","keyevent"],function(e,t,n){var r=e.View.extend({tagName:"em",dataType:"null",initialize:function(e){this.originalValue=e.originalValue},render:function(){return this.$el.text("null"),this},getValue:function(){return null}},{detect:t.isNull}),i=e.View.extend({tagName:"input",complex:!1,dataType:"boolean",attributes:{tabindex:1},initialize:function(e){this.originalValue=e.originalValue,this.$el.prop("checked",e.value).prop("type","checkbox")},getValue:function(){return this.$el.prop("checked")}},{detect:t.isBoolean}),s=e.View.extend({complex:!1,initialize:function(e){this.originalValue=e.originalValue},attributes:{tabindex:1},_choose:function(e,n){var r=this._score(e),i=this._score(n);return!r&&!i?"":(e=r>=i?e:n,Math.max(r,i)>.25?e:t.first(e))},_score:function(e){return t.isString(e)?1:t.isNumber(e)?.75:t.isNull(e)||t.isBoolean(e)||t.isEmpty(e)?0:t.isArray(e)?.25:.25}}),o=s.extend({tagName:"textarea",dataType:"string",attributes:{rows:1,tabindex:1},events:{keypress:"onKeyPress",blur:"triggerChange"},initialize:function(e){o.__super__.initialize(e),this.$el.text(this._choose(e.value,e.originalValue)),this._setRows()},_setRows:function(){this.$el.attr("rows",this.getValue().split("\n").length)},onKeyPress:function(e){e.keyCode===n.DOM_VK_ENTER&&this._setRows()},triggerChange:function(){this.trigger("change")},getValue:function(){return this.$el.prop("value")}},{detect:t.isString}),u=s.extend({attributes:{type:"number",tabindex:1},tagName:"input",dataType:"number",initialize:function(e){u.__super__.initialize(e),this.$el.prop("value",this._choose(e.value,e.originalValue))},getValue:function(){return Number(this.$el.prop("value"))},_score:function(e){return t.isNumber(e)?1:t.isString(e)?.5:0}},{detect:t.isNumber});return{number:u,string:o,"null":r,"boolean":i}})