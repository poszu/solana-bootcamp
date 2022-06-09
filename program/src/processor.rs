use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    msg,
    program::invoke_signed,
    program_error::ProgramError,
    pubkey::Pubkey,
    rent::Rent,
    system_instruction,
    sysvar::Sysvar,
};

use crate::{instruction::EchoInstruction, state::AuthorizedBufferHeader};

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction: EchoInstruction,
) -> ProgramResult {
    msg!("Processing instruction: {:?}", instruction);
    match instruction {
        EchoInstruction::Echo { data } => {
            let accounts_iter = &mut accounts.iter();
            let data_ai = next_account_info(accounts_iter)?;

            let size_to_copy = std::cmp::min(data_ai.data.borrow().len(), data.len());
            let mut buffer = data_ai.data.borrow_mut();
            buffer[..size_to_copy].copy_from_slice(&data[..size_to_copy]);

            // Zero out the remainings if any
            if size_to_copy < buffer.len() {
                buffer[size_to_copy..].fill(0);
            }
        }
        EchoInstruction::InitializeAuthorizedEcho {
            buffer_seed,
            buffer_size,
        } => {
            let accounts_iter = &mut accounts.iter();
            let authorized_buffer = next_account_info(accounts_iter)?;
            let authority = next_account_info(accounts_iter)?;
            let system_program = next_account_info(accounts_iter)?;

            let (authorized_buffer_key, bump_seed) = Pubkey::find_program_address(
                &[
                    b"authority",
                    authority.key.as_ref(),
                    &buffer_seed.to_le_bytes(),
                ],
                program_id,
            );

            if &authorized_buffer_key != authorized_buffer.key {
                msg!("Authority key doesn't match");
                return Err(ProgramError::IllegalOwner);
            }

            let account_size = AuthorizedBufferHeader::required_account_size(buffer_size);
            invoke_signed(
                &system_instruction::create_account(
                    authority.key,
                    &authorized_buffer_key,
                    Rent::get()?.minimum_balance(account_size),
                    account_size as u64,
                    program_id,
                ),
                &[
                    authority.clone(),
                    authorized_buffer.clone(),
                    system_program.clone(),
                ],
                &[&[
                    b"authority",
                    authority.key.as_ref(),
                    &buffer_seed.to_le_bytes(),
                    &[bump_seed],
                ]],
            )?;

            let authorized_buffer_header = AuthorizedBufferHeader {
                bump_seed,
                buffer_seed,
            };

            authorized_buffer_header.serialize(&mut *authorized_buffer.data.borrow_mut())?;
        }
        EchoInstruction::AuthorizedEcho { data } => {
            msg!("Authorized Echo instruction");
            let accounts_iter = &mut accounts.iter();
            let authorized_buffer = next_account_info(accounts_iter)?;
            let authority = next_account_info(accounts_iter)?;

            let authorized_buffer_header =
                AuthorizedBufferHeader::try_from_slice(&authorized_buffer.data.borrow()[..9])?;

            let (authorized_buffer_key, bump_seed) = Pubkey::find_program_address(
                &[
                    b"authority",
                    authority.key.as_ref(),
                    &authorized_buffer_header.buffer_seed.to_le_bytes(),
                ],
                program_id,
            );

            if bump_seed != authorized_buffer_header.bump_seed {
                msg!(
                    r#"Bump seed "{authorized_buffer_header.bump_seed}" doesn't match expected "{bump_seed}""#
                );
                return Err(ProgramError::InvalidAccountData);
            }
            if &authorized_buffer_key != authorized_buffer.key {
                msg!(
                    r#"Authority key "{authorized_buffer.key}" doesn't match doesn't match expected "{authorized_buffer_key}""#
                );
                return Err(ProgramError::IllegalOwner);
            }

            let buffer = &mut authorized_buffer.data.borrow_mut()[9..];
            let size_to_copy = std::cmp::min(buffer.len(), data.len());
            buffer[..size_to_copy].copy_from_slice(&data[..size_to_copy]);

            // Zero out the remainings if any
            if size_to_copy < buffer.len() {
                buffer[size_to_copy..].fill(0);
            }
        }
        EchoInstruction::InitializeVendingMachineEcho {
            price: _,
            buffer_size: _,
        } => todo!(),
        EchoInstruction::VendingMachineEcho { data: _ } => todo!(),
    }
    Ok(())
}
