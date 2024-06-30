from ninja import NinjaAPI, Schema
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import ConvoTemplate, ConvoScreen, ConvoOption
from typing import List, Optional
import logging
from ninja.errors import HttpError

api = NinjaAPI()
logger = logging.getLogger(__name__)


class OptionSchema(Schema):
    id: Optional[int] = None
    text: str
    next_screen: Optional[int] = None


class ScreenSchema(Schema):
    id: Optional[int] = None
    id_name: str
    custom_dialog_text: str
    stop_conversation: bool
    options: List[OptionSchema]


class TemplateSchema(Schema):
    id: Optional[int] = None
    name: str
    initial_screen: Optional[int] = None
    screens: List[ScreenSchema]


@api.post("/templates", response=TemplateSchema)
def create_template(request, template: TemplateSchema):
    """
    Create a new conversation template.
    """
    try:
        with transaction.atomic():
            db_template = ConvoTemplate.objects.create(name=template.name)
            screen_map = {}

            for screen_data in template.screens:
                screen = ConvoScreen.objects.create(
                    template=db_template,
                    id_name=screen_data.id_name,
                    custom_dialog_text=screen_data.custom_dialog_text,
                    stop_conversation=screen_data.stop_conversation
                )
                screen_map[screen_data.id] = screen

            for screen_data in template.screens:
                screen = screen_map[screen_data.id]
                for option_data in screen_data.options:
                    ConvoOption.objects.create(
                        screen=screen,
                        text=option_data.text,
                        next_screen=screen_map.get(option_data.next_screen)
                    )

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
            db_template.save()

            db_template.screens.all().delete()

            screen_map = {}
            for screen_data in template.screens:
                screen = ConvoScreen.objects.create(
                    template=db_template,
                    id_name=screen_data.id_name,
                    custom_dialog_text=screen_data.custom_dialog_text,
                    stop_conversation=screen_data.stop_conversation
                )
                screen_map[screen_data.id] = screen

            for screen_data in template.screens:
                screen = screen_map[screen_data.id]
                for option_data in screen_data.options:
                    ConvoOption.objects.create(
                        screen=screen,
                        text=option_data.text,
                        next_screen=screen_map.get(option_data.next_screen)
                    )

            if template.initial_screen:
                db_template.initial_screen = screen_map.get(
                    template.initial_screen)
                db_template.save()

        return _template_to_schema(db_template)
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
    Generate Lua script for a conversation template.
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
        "initial_screen": template.initial_screen.id if template.initial_screen else None,
    }
    if include_screens:
        result["screens"] = [
            {
                "id": screen.id,
                "id_name": screen.id_name,
                "custom_dialog_text": screen.custom_dialog_text,
                "stop_conversation": screen.stop_conversation,
                "options": [
                    {
                        "id": option.id,
                        "text": option.text,
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
    Generate Lua script for a given template.
    """
    lua_script = f"{template.name}_convo_template = ConvoTemplate:new {{\n"
    lua_script += f"    initialScreen = \"{
        template.initial_screen.id_name if template.initial_screen else ''}\",\n"
    lua_script += "    templateType = \"Lua\",\n"
    lua_script += f"    luaClassHandler = \"{
        template.name}ConversationHandler\",\n"
    lua_script += "    screens = {}\n"
    lua_script += "}\n\n"

    for screen in template.screens.all():
        lua_script += f"{screen.id_name} = ConvoScreen:new{{\n"
        lua_script += f"    id = \"{screen.id_name}\",\n"
        lua_script += "    left_dialog = \"\",\n"
        lua_script += f"    customDialogText = \"{
            screen.custom_dialog_text}\",\n"
        lua_script += f"    stopConversation = {
            str(screen.stop_conversation).lower()},\n"
        lua_script += "    options = {\n"

        options = list(screen.options.all())
        for i, option in enumerate(options):
            next_screen_id = option.next_screen.id_name if option.next_screen else ''
            lua_script += f"        {{\"{option.text}\", \"{next_screen_id}\"}}"
            if i < len(options) - 1:
                lua_script += ","
            lua_script += "\n"

        lua_script += "    }\n"
        lua_script += "}\n"
        lua_script += f"{template.name}_convo_template:addScreen({
            screen.id_name});\n\n"

    lua_script += f'addConversationTemplate("{template.name}_convo_template", {
        template.name}_convo_template);\n'

    return lua_script
