module MainTest exposing (suite)

import Expect
import Main
import Test exposing (Test, describe, test)
import Test.Html.Query as Query
import Test.Html.Selector exposing (class, tag, text)


suite : Test
suite =
    describe "Main Application Tests"
        [ smokeTest
        , viewTests
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
        ]
