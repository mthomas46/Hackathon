module MainTest exposing (suite)

import Expect
import Main exposing (Model, Msg(..))
import Test exposing (Test, describe, test, fuzz)
import Test.Html.Query as Query
import Test.Html.Selector exposing (class, tag, text, style)
import Fuzz exposing (string)


suite : Test
suite =
    describe "Main Application Tests"
        [ smokeTest
        , modelTests
        , updateTests
        , viewTests
        , integrationTests
        ]


smokeTest : Test
smokeTest =
    test "Main module can be imported and compiled" <|
        \_ ->
            let
                ( model, _ ) =
                    Main.init ()
            in
            Expect.equal "Hello, World! Welcome to the LLM Documentation Ecosystem!" model.message


modelTests : Test
modelTests =
    describe "Model Tests"
        [ test "initial model has correct default message" <|
            \_ ->
                let
                    ( model, _ ) =
                        Main.init ()
                in
                Expect.equal "Hello, World! Welcome to the LLM Documentation Ecosystem!" model.message
        , test "model message can be any string" <|
            \_ ->
                let
                    model =
                        { message = "Custom message" }
                in
                Expect.equal "Custom message" model.message
        ]


updateTests : Test
updateTests =
    describe "Update Tests"
        [ test "NoOp message leaves model unchanged" <|
            \_ ->
                let
                    initialModel =
                        { message = "Initial message" }

                    ( updatedModel, cmd ) =
                        Main.update NoOp initialModel
                in
                Expect.equal initialModel updatedModel
        , test "NoOp returns no command" <|
            \_ ->
                let
                    model =
                        { message = "Test message" }

                    ( _, cmd ) =
                        Main.update NoOp model
                in
                Expect.equal Cmd.none cmd
        ]


viewTests : Test
viewTests =
    describe "View Tests"
        [ test "displays the correct title" <|
            \_ ->
                let
                    ( model, _ ) =
                        Main.init ()

                    viewHtml =
                        Main.view model
                in
                viewHtml
                    |> Query.fromHtml
                    |> Query.find [ tag "h1" ]
                    |> Query.has [ text "LLM Documentation Ecosystem" ]
        , test "displays the welcome message" <|
            \_ ->
                let
                    ( model, _ ) =
                        Main.init ()

                    viewHtml =
                        Main.view model
                in
                viewHtml
                    |> Query.fromHtml
                    |> Query.find [ tag "p" ]
                    |> Query.has [ text "Hello, World! Welcome to the LLM Documentation Ecosystem!" ]
        , test "has proper container styling" <|
            \_ ->
                let
                    ( model, _ ) =
                        Main.init ()

                    viewHtml =
                        Main.view model
                in
                viewHtml
                    |> Query.fromHtml
                    |> Query.has [ class "container" ]
        , test "title has correct color styling" <|
            \_ ->
                let
                    ( model, _ ) =
                        Main.init ()

                    viewHtml =
                        Main.view model
                in
                viewHtml
                    |> Query.fromHtml
                    |> Query.find [ tag "h1" ]
                    |> Query.has [ style "color" "#2563eb" ]
        , test "container has proper max-width" <|
            \_ ->
                let
                    ( model, _ ) =
                        Main.init ()

                    viewHtml =
                        Main.view model
                in
                viewHtml
                    |> Query.fromHtml
                    |> Query.find [ class "container" ]
                    |> Query.has [ style "max-width" "800px" ]
        , test "container is centered" <|
            \_ ->
                let
                    ( model, _ ) =
                        Main.init ()

                    viewHtml =
                        Main.view model
                in
                viewHtml
                    |> Query.fromHtml
                    |> Query.find [ class "container" ]
                    |> Query.has [ style "margin" "0 auto" ]
        ]


integrationTests : Test
integrationTests =
    describe "Integration Tests"
        [ test "full application initialization and rendering" <|
            \_ ->
                let
                    ( model, cmd ) =
                        Main.init ()

                    viewHtml =
                        Main.view model
                in
                -- Test that init produces a valid model
                Expect.equal "Hello, World! Welcome to the LLM Documentation Ecosystem!" model.message
                Expect.equal Cmd.none cmd

                -- Test that view produces valid HTML
                viewHtml
                    |> Query.fromHtml
                    |> Query.has [ tag "div" ]
        , fuzz string "model can handle any message string" <|
            \randomMessage ->
                let
                    model =
                        { message = randomMessage }

                    viewHtml =
                        Main.view model
                in
                -- View should not crash with any message
                viewHtml
                    |> Query.fromHtml
                    |> Query.has [ tag "div" ]
        , test "view is idempotent - same input produces same output structure" <|
            \_ ->
                let
                    ( model1, _ ) =
                        Main.init ()

                    ( model2, _ ) =
                        Main.init ()

                    view1 =
                        Main.view model1

                    view2 =
                        Main.view model2
                in
                -- Both views should have the same structure
                view1
                    |> Query.fromHtml
                    |> Query.has [ tag "h1" ]

                view2
                    |> Query.fromHtml
                    |> Query.has [ tag "h1" ]
        ]
