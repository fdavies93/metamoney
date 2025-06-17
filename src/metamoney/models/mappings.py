from dataclasses import dataclass

@dataclass
class FieldMatchesCondition:
    field_matches: tuple[str, str] | None

@dataclass
class AllOfCondition:
    all_of: list["MappingCondition"]

@dataclass
class AnyOfCondition:
    any_of: list["MappingCondition"]

type CompoundCondition = AllOfCondition | AnyOfCondition

type MappingCondition = FieldMatchesCondition | CompoundCondition

@dataclass
class Mapping:
    when: MappingCondition
    remap: dict[str, str]
