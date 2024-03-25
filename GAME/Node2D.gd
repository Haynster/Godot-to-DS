extends Node2D

var say = "This is a godot project compiled to DS, dont press Up"
var characterValue = 0

# Called when the node enters the scene tree for the first time.
func _ready():
	characterValue = 0

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta):
	if characterValue < len(say):
		$Label.text = $Label.text + say[characterValue]
		characterValue = characterValue + 1
		await get_tree().create_timer(0.5).timeout
	if Input.is_action_just_released("ui_up"):
		$Label2.text = "fart"
