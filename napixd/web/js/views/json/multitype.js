define(["Backbone","libs/mustache"],function(e,t){var n=e.View.extend({tagName:"div",className:"json-multiedit",initialize:function(e){this.finder=e.finder,this.view=e.view,this.poppable=!!e.poppable,this.changeable=!!e.changeable},template:t.compile('<div class="json-mte btn-group">{{^changeable}}<button class="btn btn-mini disabled">{{ datatype }}</button>{{/changeable}}{{#changeable}}<button class="btn btn-mini" tabindex="3" data-type="null" >null</button><button class="btn btn-mini" tabindex="3" data-type="boolean" >bool</button><button class="btn btn-mini" tabindex="3" data-type="string" >abc</button><button class="btn btn-mini" tabindex="3" data-type="number" >123</button><button class="btn btn-mini" tabindex="3" data-type="array" >[ ]</button><button class="btn btn-mini" tabindex="3" data-type="object" >{ }</button>{{/changeable}}{{#poppable}}<button class="btn btn-mini btn-danger" tabindex="3" data-type="pop" >X</button/>{{/poppable}}</div>'),events:{"click button[data-type][data-type!='pop']":"onTranspose","click button[data-type='pop']":"pop"},render:function(){return this.$el.append(this.template({poppable:this.poppable,changeable:this.changeable,datatype:this.view.dataType})),this.$("[data-type='"+this.view.dataType+"']").addClass("active"),this.$el.append(this.view.render().el),this},getValue:function(){return this.view.getValue()},onTranspose:function(e){return this.transpose(e.target.dataset.type),this.$(":input").not(".btn").first().focus(),!1},transpose:function(e){var t=this.finder.getViewClassByType(e);this.view=new t({value:this.view.getValue(),originalValue:this.view.originalValue,finder:this.finder}),this.$el.empty(),this.render()},pop:function(){return this.trigger("pop",this),!1}});return n})