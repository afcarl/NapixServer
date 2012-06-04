define(["Backbone","underscore","jQuery","json/viewer","models/history","models/consoleentries","consoleactions"],function(a,b,c,d,e,f,g){var h=a.View.extend({tagName:"div",className:"console-entry-text ",render:function(){return c("<span />",{"class":"label"}).addClass(this.model.get("text")?"label-success":"label-danger").text(this.model.get("text")?"OK":"Fail").appendTo(this.$el),this}}),i=a.View.extend({tagName:"div",className:"console-entry-text",render:function(){return this.$el.text(this.model.get("text")),this}}),j=i.extend({tagName:"pre"}),k=a.View.extend({className:"console-entry-query",render:function(){return this.$el.append(c("<span />",{text:">>>"})).append(this.model.get("text")),this}}),l=a.View.extend({render:function(){var a=this.model.get("text");return this.$el.append((new d(a)).render().el),this}}),m=a.View.extend({initialize:function(a){this.inside=m.getView(a),this.setElement(this.inside.el)},render:function(){return this.inside.render(),this.$el.addClass("console-entry"),this}},{getView:function(a){return this.viewsMap.hasOwnProperty(a.get("level"))?new(this.viewsMap[a.get("level")])({model:a}):new this.defaultView({model:a})},viewsMap:{query:k,help:j,json:l,"boolean":h},defaultView:i}),n=a.View.extend({initialize:function(){this.setElement(c("#console-input")),this.focus(),this.keymap=this.getKeyMap(),this.$el.keypress(this.onKeyPress.bind(this)),c("#console-go").click(this.validate.bind(this)),this._historyPosition=-1,this._historyStore=""},getKeyMap:function(){return{13:this.validate,38:this.historyUp,40:this.historyDown}},onKeyPress:function(a){var b=this.keymap[a.keyCode];b&&b.call(this)},historyUp:function(){if(!e.hasMore(this._historyPosition))return;this._historyPosition===-1&&(this._historyStore=this.$el.attr("value")),this._historyPosition+=1,this.$el.attr("value",e.at(this._historyPosition).get("command"))},historyDown:function(){if(this._historyPosition===-1)return;this._historyPosition-=1,this._historyPosition===-1?this.$el.attr("value",this._historyStore):this.$el.attr("value",e.at(this._historyPosition).get("command"))},validate:function(){this._historyPosition=-1;var a=this.$el.attr("value");e.push(a),this.trigger("input",a),this.$el.attr("value",""),this.focus()},focus:function(){this.$el.focus()}}),o=a.View.extend({initialize:function(){this.setElement(c("#console-body")),f.bind("add",this.addOne,this),f.reset(),this._initActions(),c("#console-clean").click(this.clear.bind(this)),this.prompt_=new n,this.prompt_.bind("input",this.compute,this)},_initActions:function(){this.actions=b.extend({clear:this.clear,help:this.help},g),this.actions.clear.help="Clear the screen",this.actions.help.help=["Usage : help [command]","help","   Show the list of functions","help command","   Show the help of the given command"].join("\n")},compute:function(a){f.create({level:"query",text:a});var c=a.split(" ");if(!b.any(c))return;this.actions.hasOwnProperty(c[0])?this.respond(this.actions[c.shift()].apply(this,c)):f.create({level:"notfound",text:'No such method "'+c[0]+'"'})},respond:function(a){if(b.isUndefined(a))return;b.isString(a)?f.create({level:"response",text:a}):b.isBoolean(a)?f.create({level:"boolean",text:a}):f.create({level:"json",text:a})},addOne:function(a){var b=new m(a);this.$el.append(b.render().el),this.$el.scrollTop(this.$el.height())},clear:function(){this.$el.empty(),this.show()},help:function(a){this.actions.hasOwnProperty(a)?f.create({level:"help",text:this.actions[a].help}):f.create({level:"json",text:b.keys(this.actions)})},show:function(){this.prompt_.focus()}});return o})