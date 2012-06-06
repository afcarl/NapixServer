define(["jQuery","Backbone","explorer","console","selectors","libs/bootstrap"],function(a,b,c,d,e){var f=b.View.extend({el:"body",initialize:function(){this.explorer=new c,this.console=new d,this.selectors=new e,a("#explorer-label a").tab("show"),a("#console-label a").bind("shown",this.console.show.bind(this.console)),a("#firstrun a").on("click",function(){require(["firstrun"],function(a){a()})})}}),g=b.Router.extend({initialize:function(){this.panels=new f,this.panels.explorer.bind("selected",this.navigate,this)},routes:{console:"showConsole","*path/":"goToPath","*path":"goToPath","/":"showConsole"},goToPath:function(a){this.panels.explorer.goToPath(a[0]!=="/"?"/"+a:a)}});return g})