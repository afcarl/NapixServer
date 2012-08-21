define(["Backbone","underscore","jQuery","libs/mustache","views/json/viewer"],function(e,t,n,r,i){var s=e.View.extend({tagName:"textarea",className:"text-edit",initialize:function(e){this.finder=e.finder,this.value=e.value,this.types=e.types},render:function(){return this.$el.attr("value",JSON.stringify(this.value,null,4)),this},getValue:function(){var e=this._getValue();return this._check(e,this.types)},_check:function(e,n){return t.isString(n)&&this._checkSimple(e,n)?e:t.isObject(n)?this._checkObject(e,n):t.isArray(n)?this._checkArray(e,n):""},_checkObject:function(e,n){return t.isObject(e)?(e=t.chain(n).map(function(t,n){return n in e?[n,this._check(e[n],t)]:[n,""]},this).compact().objectify(),e):{}},_checkArray:function(e,t){return e},_checkSimple:function(e,t){return this.finder.getViewClassByType(t).detect(e)},_getValue:function(){try{return JSON.parse(this.el.value)}catch(e){return null}}}),o=i.extend({className:"json-edit json",finder:null,initialize:function(e){this.value=e.value,this.types=e.types,this.view=null,this.shown=""},getValue:function(){return this.view.getValue()},showText:function(){if(this.shown==="text")return;this.shown="text",this.updateValue(),this.view=new s({value:this.value,types:this.types,finder:this.finder}),this.updateView()},showBuilder:function(){if(this.shown==="builder")return;this.shown="builder",this.updateValue(),this.view=this.finder.getView(this.value,this.types),this.updateView()},updateValue:function(){this.value=this.view?this.view.getValue():this.value},updateView:function(){this.$(".json-edit-body").empty().append(this.view.render().el)},template:'<div class="json-edit-header btn-group" data-toggle="buttons-radio" ><button class="btn text">Text</button><button class="btn builder active" >Builder</button></div><div class="json-edit-body"> </div><div><button tabindex="2" class="btn btn-primary validate" >Validate</button></div>',events:{"click .text":"showText","click .builder":"showBuilder","click .validate":"validate"},render:function(){return this.$el.append(this.template),this.showBuilder(),this},validate:function(){this.trigger("validate",this.getValue())}});return{text:s,builder:o}})