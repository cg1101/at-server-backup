#
# libraries behaviour control
#
export OAUTHLIB_INSECURE_TRANSPORT=1

#
# local cookies
#
export APP_COOKIE_NAME=gnx
export APP_COOKIE_PREFIX=Cookie
export APP_COOKIE_SECRET=01342dfa/12340af/afds
export SECRET_KEY=asdfasfdas0fjasasdfl

#
# app general settings
#
export APPLICATION_CONFIG=development
export BUCKET_NAME=gnx-stage.appen.com
export CURRENT_USER_ID=1
export DATABASE_URI=postgresql://localhost/atdb_test

#
# runtime environment for client
#
export APP_ROOT_URL=http://localhost
export EDM_URL=https://edm-stage.appen.com
export GO_URL=https://go-stage.appen.com
export TIGER_URL=https://global-stage.appen.com
export NON_ADMIN_REDIRECT_URL=https://global-stage.appen.com

#
# authentication/SSO
#
export OAUTH2_CLIENT_ID=appen_global
export OAUTH2_CLIENT_SECRET=12345678910
export OAUTH2_TOKEN_ENDPOINT=http://localhost:3099/auth/tiger/access_token
export OAUTH2_AUTHORIZATION_ENDPOINT=http://localhost:3099/auth/tiger/authorize
export AUTHENTICATED_USER_INFO_URL=http://localhost:3099/auth/tiger/user.json
export AUTHENTICATION_LOGOUT_URL=http://localhost:3099/auth/tiger/invalidate
export SSO_COOKIE_NAME=appen_login_session

#
# edm subscriptions
#
export EDM_TOPIC_PERSON=arn:aws:sns:us-west-2:220211432420:EDM_PERSON_STAGE
export EDM_TOPIC_COUNTRY=arn:aws:sns:us-west-2:220211432420:EDM_COUNTRY_STAGE
export EDM_TOPIC_LANGUAGE=arn:aws:sns:us-west-2:220211432420:EDM_LANGUAGE_STAGE
export SNS_AUTHENTICATE_REQUEST=

#
# go/global/edm
#
export APPEN_API_SECRET_KEY=paz2tri45vishelZaichikPoguliat

#
# pdb api settings
# 
export PDB_API_URL=https://pdb-api.appen.com
export PDB_API_KEY=
export PDB_API_SECRET=
export USE_PDB_API=

#
# audio server
#
export AUDIO_SERVER_API_SECRET=SlMjkeR06E7Tf3S1uTFku7so21T5BR

#
# appenonline
#
export AO_WEB_SERVICES_URL=https://appenonline.appen.com.au/webservices
export AO_WEB_SERVICES_KEY=YDhL2qjgdJXfWyAekaQAbJM5BQnDhNzio1gJaE3AxYhQsGsvmnNzItmnMmCAdvbKJn70uCRgMJj7hoVvXp8swkkic1dQpLdQ99A0fPocTbmztBHKnstPa2zScavug3KcJ5Odt1G595YppzCCPBkyINeQ5ooWkekmBh85mxEk17dehosZHsLZWONCBdg4M42b6gl6KoD2WZxXsIW8KkVDVQ7cD3eHYuJQX48GtGu7jhnAULL0UyCOvlfQhdICAcQusR9CC7tsmF2Siq0YN6FNfdWgLTAwFJWaLtIPeolOz0NCUYdNKwaZ13zDZ2KKEPku1zcHd2jtE4HmFAe0q7mEpJp1g8JZPyHipp2quHM4kG1sYP25F5cvxfGKzKC3SvFzdWQezWBETkcftOr7vRzyXcDDt6BMb5OjRCrqwZfhHPik7KL79S2VQWARNmQrMN4Do35FYjtZd7ECPqg8GhRp5Fnup0VBfD1s0bWLbJXUEGFYA9rhm9SaijKcWFMfT8jX
