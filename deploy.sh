sam build \
	--use-container \
	--no-cached

sam deploy \
	--no-confirm-changeset \
	--no-fail-on-empty-changeset
