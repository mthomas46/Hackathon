module Main exposing (main, init, update, view, Model, Msg)

import Browser
import Html exposing (Html, div, h1, p, text)
import Html.Attributes exposing (class, style)


type alias Model =
    { message : String
    }


type Msg
    = NoOp


init : () -> ( Model, Cmd Msg )
init _ =
    ( { message = "Hello, World! Welcome to the LLM Documentation Ecosystem!" }
    , Cmd.none
    )


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        NoOp ->
            ( model, Cmd.none )


view : Model -> Html Msg
view model =
    div
        [ class "container"
        , style "font-family" "Arial, sans-serif"
        , style "max-width" "800px"
        , style "margin" "0 auto"
        , style "padding" "2rem"
        , style "text-align" "center"
        ]
        [ h1
            [ style "color" "#2563eb"
            , style "margin-bottom" "2rem"
            ]
            [ text "LLM Documentation Ecosystem" ]
        , div
            [ style "background-color" "#f3f4f6"
            , style "padding" "2rem"
            , style "border-radius" "8px"
            , style "border" "1px solid #e5e7eb"
            ]
            [ p
                [ style "font-size" "1.25rem"
                , style "margin" "0"
                ]
                [ text model.message ]
            ]
        ]


main : Program () Model Msg
main =
    Browser.element
        { init = init
        , update = update
        , view = view
        , subscriptions = \_ -> Sub.none
        }
