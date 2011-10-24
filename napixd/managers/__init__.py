#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.exceptions import ValidationError

"""
Manager :
    - manages a set of resources
    - does it by defining create/delete/modify methods that act on those resources
Ressource :
    - MUST be a dict (or an emulation thereof) that hold a set of properties
    - They MAY

Manager are created by the corresponding resource
"""

class Manager(dict):
    """
    Base class of the managers

    Managers are objects created to serve requests on a resource for its sub resources
    exemple:
    GET /physics/constants/c
    A manager is created of the resource `physics`, this resource is asked for its child `constants`,
    a manager for this resource `constant` is created, and this manager is asked for its child `c`.
    The resource got is serialized and sent back to the user

    Managers cycle of life MAY contains multiple request, that MAY be executed simultaneously.

    The cycle of life is :
    -Class creation
    -Insertion into the application inside the root manager or through a parent manager
    -Manager.configure is called with the settings of this class
    -\ An instance is generated for a resource
      | / start_request is called
      | | the appropriate method to respond to the request is called (get_resource, create_resource, etc)
      | \ end_request is called

    Subclasses  MAY set a managed_class class attribute. If set, it must be a class inheriting from
    this same base class (or implementing its interface).
    When using going up of a level in the url, children are wrapped in this class

    If it's not set, the manager does not have sub resources

    example
    >>>class FirstManager(Manager):
    >>>     managed_class = SecondManager

    >>>class SecondManager(Manager):
    >>>     def list_resource(self):
    >>>         return {}

    GET /first/second/third
    >>>second_resource = FirstManager.get_resource('second')
    >>>second_manager = SecondManager(second_resource)
    >>>return second_manager.get_resource('third')

    GET /first/second/third/
    404 NOT FOUND
    GET /first/second/third/fourth
    404 NOT FOUND

    Subclasses of this class MUST define their own list of fields
    in the class attribute resource_fields.

    This attribute is a dict where the keys are the fields names and the values are
    the descriptions of those fields

    properties includes:
        -optional : if the value is optional
        -example : used for documentation and the example resource
        -description : describe the use of the resource
    example:
    >>>class User(Manager):
    >>>     resource_fields = {
    >>>         'username':{'description':'POSIX username of the system account', 'example':'dritchie'},
    >>>         'uid':{'description':'Unique identifier, will be generated if not given','optional':True},
    >>>         'gecos':{'description':'Comment on the user name',example:'Dennis M. Ritchie'}
    >>>         }

    The resources may contains some fields that are not in the class' resource_fields.
    When the resource are serialized to be send in json,
    only the fields in resource_fields are extracted.

    This behavior may be usefull to pass privates values to the next managers.
    exemple
    >>>class SectionManager(Manager):
    >>>     def list_resource(self):
    >>>         return self.parent['parser'].get_sections()
    >>>class File(Manager):
    >>>     managed_class = SectionManager
    >>>     fields = { 'path':'{} }
    >>>     def get_resource(self,id):
    >>>         return {'parser':Parser('/etc/'+id),'path':'/etc'+id}

    GET /file/file1
    { "path" : "/etc/file1" }
    #No parser field sent

    GET /file/file1/
    [ "section1" , "section2"]
    #Parser was passed to list_resource through parent

    """

    #list of the fields publicly available with their properties
    resource_fields = {}
    #Class wraping the children
    managed_class = None

    def __init__(self,parent):
        """
        intialize the Manager with the parent resource creating it

        example
        >>>class FirstManager(Manager):
        >>>     managed_class = SecondManager

        >>>class SecondManager(Manager):
        >>>     def list_resource(self):
        >>>         return {}

        GET /first/second/
        >>> SecondManager(FirstManager.get_resource('second')).list_resource()

        """
        self.parent = parent

    @classmethod
    def configure(cls,conf):
        """
        Method called with the configuration of this class
        """
        pass

    def get_example_resource(self):
        """
        Generate an example of the resources managed by this manager
        Computed by the `example` of each resource field in Manager.resource_fields
        """
        example = {}
        for field,description in self.resource_fields:
            example[field]= description.get('example',None)
        return example

    def validate_id(self,id_):
        """
        Check that the id given as an argument is a valid ID

        The id is always a string extracted from the url.

        if the id is not valid, raises a ValidationError
        if necessary, modify the id
        this method MUST return the ID even if it wasn't modified.

        example:
        if the id must be an int
        >>> class IntID(Manager):
        >>>     def validate_id(self,id_):
        >>>         try:
        >>>             return int(id_)
        >>>         except ValueError:
        >>>             raise ValidationError

        if the id must be a string containing at least 3 charcters
        >>>class MinLength(Manager):
        >>>     def validate_id(self,id_):
        >>>         if len(id_) < 3:
        >>>             raise ValidationError
        >>>         #always return the id
        >>>         return id_

        By default, this method checks if the id is not an empty string
        """
        if id_ == '':
            raise ValidationError
        return id_

    def validate_resource(self, resource_dict):
        """
        Validate a resource_dict (which can be directly a dict or an object emulating a dict) by
        checking that every mandatory field specified in self.resource_fields is defined.

        If the current object implement self.validate_resource_<key> method, it'll be called with
        the value of resource_dict[<key>] as parameters.
        It shoud raise a ValidationError if the data isn't valid, else it must return a valid value

        Return a resource_dict.
        """
        # Create a new dict to populate with validated data
        for key, description in self.resource_fields:
            if "optional" not in description and key not in resource_dict:
                raise ValidationError("Field %s is missing in the supplied resource"%key)
            validator = getattr(self, 'validate_resource_%s'%key,None)
            if validator:
                resource_dict[key] = validator(resource_dict.get(key,None))
        return resource_dict

    def start_request(self,request):
        """
        place holder method that is called at the start of each HTTP request
        """
        pass
    def end_request(self,request):
        """
        place holder method that is called at the end of each HTTP request
        """
        pass

class ManagerInterface(Manager):
    """
    HTTP calls map

    This interface MUST NOT be inherited by the subclasses.

    The managers MAY not implement all the methods below.
    The method not implemented will be answered by a 405 METHOD NOT ALLOWED response
    with the list of methods auhorized computed according to the existing methods.

    If a attribute or a method of the manager has one of those methods name, the functionnality
    will be considered being implemented.

    The manager MUST NOT define a method with a raise NotImplementedError
    to mean that the method is not supported.
    """
    def delete_resource(self,resource_id):
        """
        Delete a managed ressource.

        Eg :
        DEL /something/[...]/mymanager/42
        will be translated to :
        mymanager.delete_resource('42')

        """
        raise NotImplementedError

    def create_resource(self, resource_dict):
        """
        Create a new managed ressource.

        resource_id parameters is either the id given in the URL, if present, or the result of
        self.new_resource_id(self, resource_dict)

        resource_dict is a dict populated with PUT/POSTED json resource_dict.

        Eg:
        POST /something/[...]/mymanager/ with resource_dict { 'toto': 1 }
        will be translated to :
        mymanager.create_resource({ 'toto': 1})
        """
        raise NotImplementedError

    def get_resource(self,resource_id):
        """
        Get the ressource object corresponding to resource_id.

        This object must be a dict or emulate it, as the nAPIxd will convert this dict
        to a json object to build his response.

        Eg: GET /somehting/[...]/mymanager/42
        call
        mymanager.get_resource(self, '42')

        """
        raise NotImplementedError


    def modify_resource(self,resource_id,resource_dict):
        """
        Modify the ressource designed by resource_id by updating it with resource_dict
        defined values.

        If modify_resource is not defined, it's emulated by calling delete/create sequentially.

        Eg: PUT /something/[...]/mymanager/42
        will be translated to :
        mymanager.modify_resource('42', { 'toto': 4242 })
        """
        raise NotImplementedError

    def list_resource(self):
        """
        Return the ids list of all managed resource. The result can be of 2 form : either a direct list
        of string, representing each id, or a list of dict, defining at least '_id' and '_desc' as key.

        Eg: GET /something/[...]/mymanager/
        will be translated to
        mymanager.list_resource_id()

        After processing, the nAPIx daemon will always convert the list in a list of dict, and add
        the _uri key with appropriate value (based on baseurl + _id).
        """
        raise NotImplementedError