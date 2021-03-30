import chevron
from textwrap import dedent

# bruh
camelcase = lambda test_str: test_str[:1].lower() + test_str[1:] if test_str else '' 

class EternalEvent:
    template = dedent("""\
        eventCall = {
            eventDef = "{{name}}";
            args = {
                num = {{count}};
                {{#items}}
                item[{{index}}] = {
                    {{var}} = {{{value}}};
                }
                {{/items}}
            }
        }
    """)

    def stringify(self):
        items = [
            {
                "index": index, 
                "value": f'"{val[1]}"' if isinstance(val[1], str) and val[1] != "NULL" else val[1], 
                "var": var[1]
            }
            for index, (val, var) in enumerate(zip(vars(self).items(), self.args))
        ]
        return chevron.render(template=self.template, data={"name":camelcase(type(self).__name__), "items":items, "count":len(items)})
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        args = []
        for attr, value in cls.__dict__.items():
            if not attr.startswith('__'):
                args.append((attr,value))
        cls.args = args
        
    def __str__(cls):
            return cls.stringify()
        
    def __init__(self, *args):
        for init_arg, (cls_name, cls_args) in zip(args, self.args):
            setattr(self, cls_name, init_arg)
            
# I should probably not do this lol
class MaintainAICount(EternalEvent):
    spawnType: str = "eEncounterSpawnType_t"
    desired_count: str = "int"
    max_spawn_count: str = "int"
    min_spawn_delay: str = "float"
    min_ai_for_respawn: str = "int"
    spawnGroup: str = "entity"
    group_level: str = "string"
    max_spawn_delay: str = "float"

class SpawnAI(EternalEvent):
    spawnType: str = "eEncounterSpawnType_t"
    spawn_count: str = "int"
    spawnGroup: str = "idTargetSpawnGroup"
    group_label: str = "char"
        
class SetMusicState(EternalEvent):
    target: str = "idMusicEntity"
    stateDecl: str = "idSoundState"
    designComment: str = "char"
        
class Wait(EternalEvent):
    seconds: str = "float"
    disableAIHighlight: str = "bool"
        
class WaitAIHealthLevel:
    aiType: str = "eEncounterSpawnType_t"
    desired_remaing_ai_count: str = "int"
    group_label: str = "char"
    disableAIHighlight: str = "bool"