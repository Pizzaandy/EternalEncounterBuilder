import chevron
from textwrap import dedent

# bruh
camelcase = lambda test_str: test_str[:1].lower() + test_str[1:] if test_str else ''

# (alias, total_args, optional_args)
event_to_ebl = {}
ebl_to_event = {}


class EternalEvent:
    ev_template = dedent("""\
        eventCall = {
            eventDef = "{{name}}";
            args = {
                num = {{count}};
                {{#items}}
                item[{{index}}] = {
                    {{var}} = {{{value}}}
                }
                {{/items}}
            }
        }
    """)

    decl_template = dedent("""\
        {
                        {{varname}} = {{{value}}}
                    }""")

    def stringify(self):
        items = [
            {
                "index": index,
                "value": (f'"{val[1]}";' if isinstance(val[1], str)
                          and val[1] not in ["NULL", "true", "false"]
                          else f'{val[1]};'),
                "var": var[1]
            }
            for index, (val, var) in enumerate(zip(vars(self).items(), self.args))
        ]
        #print(items)
        name = camelcase(type(self).__name__)
        for item in items:
            if item["var"].startswith("decl"):
                varname = item["var"].replace("decl = ", "")
                item["var"] = "decl"
                item["value"] = (
                    chevron.render(
                        template=self.decl_template,
                        data={"varname": varname, "value": item["value"]}))

        return chevron.render(
            template=self.ev_template,
            data={"name": name, "items": items, "count": len(items)})

    def __init_subclass__(cls, alias="", **kwargs):
        super().__init_subclass__(**kwargs)
        # initialize fields
        args = []
        optional_args = 0
        for attr, value in cls.__dict__.items():
            if not attr.startswith("__"):
                if value[-1] == "*":
                    value = value.replace("*", "")
                    optional_args += 1
                args.append((attr, value))
        cls.args = args
        # add event class aliases to dicts
        _default_alias = camelcase(cls.__name__)
        _alias = alias if alias else [camelcase(cls.__name__)]
        if not isinstance(_alias, list):
            _alias = [_alias]
        event_to_ebl[cls.__name__] = (_alias[0], len(args), optional_args)

        for item in _alias:
            ebl_to_event[item] = (cls.__name__, len(args))
        ebl_to_event[_default_alias] = (cls.__name__, len(args))

    def __init__(self, *args):
        for init_arg, (cls_name, cls_args) in zip(args, self.args):
            setattr(self, cls_name, init_arg)

    def __str__(cls):
        return cls.stringify()


class MaintainAICount(EternalEvent, alias=["maintainAI", "maintain"]):
    spawnType: str = "eEncounterSpawnType_t"
    desired_count: str = "int"
    max_spawn_count: str = "int"
    min_spawn_delay: str = "float"
    min_ai_for_respawn: str = "int"
    spawnGroup: str = "entity"
    group_level: str = "string"
    max_spawn_delay: str = "float"

class StaggeredAISpawn(EternalEvent):
    spawnType: str = "eEncounterSpawnType_t"
    spawn_count:  str = "int"
    spawnGroup: str = "entity*"
    group_label: str = "string*"
    minSpawnStagger: str = "float"
    maxSpawnStagger: str = "float"

class StopMaintainingAICount(EternalEvent, alias = "stopMaintainAI"):
    spawnType: str = "eEncounterSpawnType_t"
    group_label: str = "string*"

class SpawnAI(EternalEvent):
    spawnType: str = "eEncounterSpawnType_t"
    spawn_count: str = "int"
    spawnGroup: str = "entity"
    group_label: str = "string"

class SpawnSingleAI(EternalEvent, alias = "spawn"):
    spawnType: str = "eEncounterSpawnType_t"
    spawnTarget: str = "entity"
    group_label: str = "string*"

class SetMusicState(EternalEvent):
    target: str = "entity"
    stateDecl: str = "decl = soundstate"
    designComment: str = "string"

class MakeAIAwareOfPlayer(EternalEvent, alias = "alertAI"):
    allActive: str = "bool"
    onSpawn: str = "bool"
    groupLabel: str = "string*"
    restorePerception: str = "bool"

class ActivateTarget(EternalEvent, alias = "activate"):
    targetEntity: str = "entity"
    command: str = "string"

class SetFactionRelation(EternalEvent):
	instigatorSpawnType: str = "eEncounterSpawnType_t"
	groupLabel: str = "string*"
	targetSpawnType: str = "eEncounterSpawnType_t"
	relation: str = "socialEmotion_t"

class ClearFactionOverrides(EternalEvent):
    pass

class ForceChargeOnAllAI(EternalEvent):
    pass

class WaitMulitpleConditions(EternalEvent):
    condition_count: str = "int"
    logic_operator: str = "encounterLogicOperator_t"
    disableAIHighlight: str = "bool"

class Wait(EternalEvent):
    seconds: str = "float"
    disableAIHighlight: str = "bool"

class WaitAIHealthLevel(EternalEvent):
    aiType: str = "eEncounterSpawnType_t"
    desired_remaing_ai_count: str = "int"
    group_label: str = "char"
    disableAIHighlight: str = "bool"

class WaitAIRemaining(EternalEvent, alias = "AIRemaining"):
    aiType: str = "eEncounterSpawnType_t"
    desired_count: str = "int"
    group_label: str = "string"

class WaitMaintainComplete(EternalEvent, alias = "maintainComplete"):
    aiType: str = "eEncounterSpawnType_t"
    remaining_spawn_couunt: str = "int"
    group_label: str = "string"

class WaitForEventFlag(EternalEvent, alias = "Flag"):
    eventFlag: str = "eEncounterEventFlags_t"
    userFlag: str = "string*"
    testIfAlreadyRaised: str = "bool"
    disableAIHighlight: str = "bool"

class DamageAI(EternalEvent):
    damageType: str = "decl = damage"
    aiType: str = "eEncounterSpawnType_t"
    group_label: str = "string*"

class DesignerComment(EternalEvent, alias = "print"):
	designerComment: str = "string*"
	printToConsole: str = "bool"

#events = []
#for line in lines:
    #if line.startswith("Wave"):

#mylist = get_event_args(SpawnAI)
#print(mylist
