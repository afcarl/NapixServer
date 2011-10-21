#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Lock

from napixd.exceptions import NotFound,Duplicate,ValidationError

from . import Manager

class ReadOnlyDictManager(Manager):
    """
    Manager that manages a list (or a dict) of objects

    Once it's created, it manage a internal list of resources.
    This list of resources is generated by the method `load` that must be overriden.
    It is saved in the manager and used to serve the basic operations

    The list of resources must be an indexable object.
    The id of the resources must be the index of the resource in the internal list.

    This manager give only access to resources in for GET request
    """

    #Methods to override
    def load(self,parent):
        """
        Load: Return the list of the resources managed by this manager
        take the parent that created this manager instance as argument

        example:

        >>>class CountryManager(ListManager):
        >>>     def load(self,parent):
        >>>         f=open('/'+parent['galaxy']+'/'+parent['planet'],'r')
        >>>         countries = []
        >>>         for x in f.readline():
        >>>             countries.append(x)
        >>>         return x

        GET /worlds/earth/france
        >>>parent = WorldManager().get_resource('earth')
        >>>parent
        World { 'name':'planet', 'galaxy': 'Milky Way'}
        >>>earth_countries = CountryManager(parent)
        >>>earth_countries.get_resource('france')
           earth_countries.load({'name':'earth','galaxy':'Milky Way'})

        """
        raise NotImplementedError

    def _get_resources(self):
        if not hasattr(self,'_resources'):
            self._resources = self.load(self.parent)
        return self._resources
    def _set_resources(self,value):
        self._resources = value
    #resources are lazy loaded
    resources = property(_get_resources,_set_resources)

    def get_resource(self,resource_id):
        try:
            return self.resources[resource_id]
        except KeyError:
            raise NotFound

    def list_resource(self):
        return self.resources.keys()

class DictManager(ReadOnlyDictManager):
    """
    Manager for a dictionary of resources.

    This manager inherits of the read-only version and add support for modifications
    When the resources list is modified, the method `save` is called to persist the resources

    The id of a new resource is generated by the method `generate_new_id`.
    """

    def __init__(self,parent):
        super(DictManager,self).__init__(parent)
        #lock to avoid race conditions
        self.resource_lock = Lock()

    def save(self,parent,content):
        """
        Save the ressources after they have been altered by the user's request.
        Idempotent methods (GET,HEAD) don't trigger the save

        >>>class CountryManager(ListManager):
        >>>     def save(self,parent,ressources):
        >>>         f=open('/'+parent['galaxy']+'/'+parent['planet'],'w')
        >>>         countries = []
        >>>         for x in resources:
        >>>             countries.write(x)
        >>>             countries.write('\n')

        """
        raise NotImplementedError

    def generate_new_id(self,resource_dict):
        """
        Generate a new identifier for the resource dict given
        It must be overriden by the sub classes
        """
        raise NotImplementedError

    #private methods and attributes


    def end_request(self,request):
        """
        overrides the parent's method to save the ressources after every request
        that may have altered the datas
        """
        if request.method not in ('GET','HEAD'):
            self.save(self.resources)


    def _set_resource(self,resource_id,resource_dict):
        """
        Set a resource inside the resources list
        """
        self.resources[resource_id] = resource_dict


    def modify_resource(self,resource_id,resource_dict):
        with self.resource_lock:
            resource = self.get_resource(resource_id)
            resource.update(resource_dict)
            self._set_resource(resource_dict,resource_id)

    def create_resource(self,resource_dict):
        with self.resource_lock:
            resource_id = self.generate_new_id(resource_dict)
            if resource_id in self.resources:
                raise Duplicate
            self._set_resource(resource_id,resource_dict)
            return resource_id

    def delete_resource(self,resource_id):
        with self.resource_lock:
            try:
                self.resources.pop(resource_id)
            except KeyError:
                raise NotFound

class ListManager(DictManager):
    """
    Manager that manages a list of resources
    """
    def create_resource(self,resource_dict):
        with self.resource_lock:
            self.resources.append(resource_dict)
            return len(self.resources) - 1

    def validate_id(self):
        """
        Override the parent method to limit id to integer values
        """
        try:
            return int(self)
        except  (ValueError,TypeError):
            raise ValidationError('This resource ids are integers')
