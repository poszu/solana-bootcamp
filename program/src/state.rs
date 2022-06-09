use borsh::{BorshDeserialize, BorshSerialize};

#[derive(BorshSerialize, BorshDeserialize, Debug, Clone)]
pub struct AuthorizedBufferHeader {
    pub bump_seed: u8,
    pub buffer_seed: u64,
}

impl AuthorizedBufferHeader {
    pub fn required_account_size(buffer_size: usize) -> usize {
        1 + 8 + buffer_size
    }
}
