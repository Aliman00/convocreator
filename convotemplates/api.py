from ninja import NinjaAPI, Schema
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import ConvoTemplate, ConvoScreen, ConvoOption
from typing import List, Optional
import logging
from ninja.errors import HttpError
from stfwriter import STFWriter
from io import BytesIO
from django.http import HttpResponse

api = NinjaAPI()
logger = logging.getLogger(__name__)

# Schema definitions


class STFPayload(Schema):
    templateName: str
    data: List[List[str]]


class OptionSchema(Schema):
    id: Optional[int] = None
    text: str
    stfReference: Optional[str] = None
    next_screen: Optional[int] = None


class ScreenSchema(Schema):
    id: Optional[int] = None
    id_name: str
    custom_dialog_text: str
    leftDialog: Optional[str] = None
    stop_conversation: bool
    options: List[OptionSchema]


class TemplateSchema(Schema):
    id: Optional[int] = None
    name: str
    stf_mode: bool
    initial_screen: Optional[int] = None
    screens: List[ScreenSchema]


@api.post("/templates/stf")
def create_stf_file(request, payload: STFPayload):
    """
    Create an STF file from the provided data and return it for download.
    """
    try:
        writer = STFWriter()
        template_name = payload.templateName
        data = payload.data

        # Use BytesIO to store the file in memory
        stf_buffer = BytesIO()
        writer.save_data(data, stf_buffer)

        # Create a response with the STF file
        response = HttpResponse(stf_buffer.getvalue(),
                                content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{
            template_name}.stf"'
        return response
    except Exception as e:
        logger.error(f"Error creating STF file: {str(e)}")
        raise HttpError(400, f"Error creating STF file: {str(e)}")


@api.post("/templates", response=TemplateSchema)
def create_template(request, template: TemplateSchema):
    """
    Create a new conversation template.
    """
    try:
        with transaction.atomic():
            db_template = ConvoTemplate.objects.create(name=template.name)
            screen_map = {}

            # Create screens
            for screen_data in template.screens:
                screen = ConvoScreen.objects.create(
                    template=db_template,
                    id_name=screen_data.id_name,
                    custom_dialog_text=screen_data.custom_dialog_text,
                    stop_conversation=screen_data.stop_conversation
                )
                screen_map[screen_data.id] = screen

            # Create options and link screens
            for screen_data in template.screens:
                screen = screen_map[screen_data.id]
                for option_data in screen_data.options:
                    ConvoOption.objects.create(
                        screen=screen,
                        text=option_data.text,
                        next_screen=screen_map.get(option_data.next_screen)
                    )

            # Set initial screen
            if template.initial_screen:
                db_template.initial_screen = screen_map.get(
                    template.initial_screen)
                db_template.save()

        return _template_to_schema(db_template)
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HttpError(400, f"Error creating template: {str(e)}")


@api.put("/templates/{template_id}", response=TemplateSchema)
def update_template(request, template_id: int, template: TemplateSchema):
    """
    Update an existing conversation template.
    """
    try:
        with transaction.atomic():
            db_template = get_object_or_404(ConvoTemplate, id=template_id)
            db_template.name = template.name
            db_template.stf_mode = template.stf_mode
            db_template.save()

            # Remove existing screens and options
            db_template.screens.all().delete()

            screen_map = {}
            # Create new screens
            for screen_data in template.screens:
                screen = ConvoScreen.objects.create(
                    template=db_template,
                    id_name=screen_data.id_name,
                    custom_dialog_text=screen_data.custom_dialog_text,
                    leftDialog=screen_data.leftDialog,
                    stop_conversation=screen_data.stop_conversation
                )
                screen_map[screen_data.id] = screen

            # Create new options and link screens
            for screen_data in template.screens:
                screen = screen_map[screen_data.id]
                for option_data in screen_data.options:
                    ConvoOption.objects.create(
                        screen=screen,
                        text=option_data.text,
                        stfReference=option_data.stfReference,
                        next_screen=screen_map.get(option_data.next_screen)
                    )

            # Set initial screen
            if template.initial_screen:
                db_template.initial_screen = screen_map.get(
                    template.initial_screen)
                db_template.save()

        return _template_to_schema(db_template, include_screens=True)
    except Exception as e:
        raise HttpError(400, f"Error updating template: {str(e)}")


@api.delete("/templates/{template_id}")
def delete_template(request, template_id: int):
    """
    Delete a conversation template.
    """
    try:
        template = get_object_or_404(ConvoTemplate, id=template_id)
        template.delete()
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}")
        raise HttpError(400, f"Error deleting template: {str(e)}")


@api.get("/templates/{template_id}/lua")
def generate_lua(request, template_id: int):
    """
    Generate a Lua script for the given template.
    """
    try:
        template = get_object_or_404(ConvoTemplate, id=template_id)
        lua_script = _generate_lua_script(template)
        return {"lua_script": lua_script}
    except Exception as e:
        logger.error(f"Error generating Lua script: {str(e)}")
        raise HttpError(400, f"Error generating Lua script: {str(e)}")


@api.get("/templates", response=List[TemplateSchema])
def list_templates(request):
    """
    List all conversation templates.
    """
    templates = ConvoTemplate.objects.all()
    return [_template_to_schema(t, include_screens=False) for t in templates]


@api.get("/templates/{template_id}", response=TemplateSchema)
def get_template(request, template_id: int):
    """
    Get a specific conversation template.
    """
    template = get_object_or_404(ConvoTemplate, id=template_id)
    return _template_to_schema(template)


def _template_to_schema(template: ConvoTemplate, include_screens: bool = True) -> dict:
    """
    Convert a ConvoTemplate instance to a dictionary matching TemplateSchema.
    """
    result = {
        "id": template.id,
        "name": template.name,
        "stf_mode": template.stf_mode,
        "initial_screen": template.initial_screen.id if template.initial_screen else None,
    }
    if include_screens:
        result["screens"] = [
            {
                "id": screen.id,
                "id_name": screen.id_name,
                "custom_dialog_text": screen.custom_dialog_text,
                "leftDialog": screen.leftDialog,
                "stop_conversation": screen.stop_conversation,
                "options": [
                    {
                        "id": option.id,
                        "text": option.text,
                        "stfReference": option.stfReference,
                        "next_screen": option.next_screen.id if option.next_screen else None
                    } for option in screen.options.all()
                ]
            } for screen in template.screens.all()
        ]
    else:
        result["screens"] = []
    return result


def _generate_lua_script(template: ConvoTemplate) -> str:
    """
    Generate a Lua script for the given template.
    """
    lua_script = f"{template.name}ConvoTemplate = ConvoTemplate:new {{\n"
    lua_script += f"    initialScreen = \"{
        template.initial_screen.id_name if template.initial_screen else ''}\",\n"
    lua_script += "    templateType = \"Lua\",\n"
    lua_script += f"    luaClassHandler = \"{template.name}ConvoHandler\",\n"
    lua_script += "    screens = {}\n"
    lua_script += "}\n\n"

    for screen in template.screens.all():
        lua_script += f"{screen.id_name} = ConvoScreen:new{{\n"
        lua_script += f"    id = \"{screen.id_name}\",\n"

        if template.stf_mode and screen.leftDialog:
            lua_script += f"    leftDialog = \"{screen.leftDialog}\",\n"
        else:
            lua_script += f"    leftDialog = \"{
                screen.custom_dialog_text}\",\n"

        lua_script += f"    stopConversation = \"{
            str(screen.stop_conversation).lower()}\",\n"
        lua_script += "    options = {\n"

        options = list(screen.options.all())
        for i, option in enumerate(options):
            next_screen_id = option.next_screen.id_name if option.next_screen else ''

            option_text = option.stfReference if template.stf_mode and option.stfReference else option.text

            lua_script += f"        {{\"{option_text}\", \"{next_screen_id}\"}}"
            if i < len(options) - 1:
                lua_script += ","
            lua_script += "\n"

        lua_script += "    }\n"
        lua_script += "}\n"
        lua_script += f"{template.name}ConvoTemplate:addScreen({
            screen.id_name});\n\n"

    lua_script += f"addConversationTemplate(\"{template.name}ConvoTemplate\", {
        template.name}ConvoTemplate);\n"

    return lua_script
