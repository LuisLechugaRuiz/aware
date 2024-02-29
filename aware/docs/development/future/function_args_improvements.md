# Function args improvements

As commented during [Feb 29 - Function args](/aware/docs/development/calendar/february/29.md#complex-args-on-function-call) we need to be able to add arbitrary types to function calling, this will enable more complex requests and functions. It would follow a Object-oriented approach to be able to use higher level abstractions and therefore get a hierarchical representation of the inputs.

Should we done after initial version, as an enhancement to current system. Involve a small adaptation on PydanticParser and a refactor on requests format to allow creating requests using other request formats as primitives (ros style but cleaner with our integration with Supabase).